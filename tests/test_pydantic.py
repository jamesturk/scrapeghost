import pytest
from pydantic import BaseModel, ValidationError
from scrapeghost.scrapers import SchemaScraper
from scrapeghost.errors import PostprocessingError
from scrapeghost.response import Response
from scrapeghost.postprocessors import PydanticPostprocessor


class CrewMember(BaseModel):
    name: str
    role: str
    home_planet: str


def test_pydantic_schema():
    # if a pydantic model is passed to the SchemaScraper,
    # it should be able to generate a schema from it
    # and add the PydanticPostprocessor to the postprocessors
    scraper = SchemaScraper(CrewMember)
    assert scraper.json_schema == {
        "title": "CrewMember",
        "type": "object",
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "role": {"title": "Role", "type": "string"},
            "home_planet": {"title": "Home Planet", "type": "string"},
        },
        "required": ["name", "role", "home_planet"],
    }
    assert isinstance(scraper.postprocessors[1], PydanticPostprocessor)
    assert scraper.postprocessors[1].pydantic_model == CrewMember


def test_pydantic_postprocessor_good():
    # JSON should already be parsed by the JSONPostprocessor
    # before pydantic
    resp = Response(
        data={"name": "Zorak", "role": "Band Leader", "home_planet": "Dokar"}
    )

    pdp = PydanticPostprocessor(CrewMember)
    # does not need scraper param
    resp = pdp(resp, None)

    assert resp.data == CrewMember(
        name="Zorak", role="Band Leader", home_planet="Dokar"
    )


def test_pydantic_postprocessor_invalid():
    # JSON should already be parsed by the JSONPostprocessor
    # before pydantic
    resp = Response(
        data={
            "name": "Zorak",
            "role": "Band Leader",
            #    "home_planet": "Dokar",
        }
    )

    pdp = PydanticPostprocessor(CrewMember)
    with pytest.raises(ValidationError):
        resp = pdp(resp, None)


def test_pydantic_non_dict():
    resp = Response(data="not a dict")

    with pytest.raises(PostprocessingError):
        pdp = PydanticPostprocessor(CrewMember)
        resp = pdp(resp, None)
