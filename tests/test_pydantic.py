import pytest
from pydantic import BaseModel, ValidationError
from scrapeghost.scrapers import SchemaScraper, _pydantic_to_simple_schema
from scrapeghost.errors import PostprocessingError
from scrapeghost.responses import Response
from scrapeghost.postprocessors import PydanticPostprocessor


class CrewMember(BaseModel):
    name: str
    role: str
    home_planet: str
    age: int = 0


class CrewMemberExtended(CrewMember):
    friends: list[str]
    captain: CrewMember


def test_pydantic_to_simple_schema_basics():
    assert _pydantic_to_simple_schema(CrewMember) == {
        "name": "str",
        "role": "str",
        "home_planet": "str",
        "age": "int",
    }


def test_pydantic_to_simple_schema_complex():
    assert _pydantic_to_simple_schema(CrewMemberExtended) == {
        "name": "str",
        "role": "str",
        "home_planet": "str",
        "age": "int",
        "friends": "list[str]",
        "captain": {
            "name": "str",
            "role": "str",
            "home_planet": "str",
            "age": "int",
        },
    }


def test_pydantic_schema_scrape():
    # if a pydantic model is passed to the SchemaScraper,
    # it should be able to generate a schema from it
    # and add the PydanticPostprocessor to the postprocessors
    scraper = SchemaScraper(CrewMember)
    assert scraper.json_schema == {
        "name": "str",
        "role": "str",
        "home_planet": "str",
        "age": "int",
    }
    assert isinstance(scraper.postprocessors[-1], PydanticPostprocessor)
    assert scraper.postprocessors[-1].pydantic_model == CrewMember


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
        name="Zorak",
        role="Band Leader",
        home_planet="Dokar",
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
