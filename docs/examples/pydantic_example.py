from pydantic import BaseModel
from scrapeghost import SchemaScraper, CSS


class CrewMember(BaseModel):
    gender: str
    race: str
    alignment: str


# passing a pydantic model to the SchemaScraper # will generate a schema from it
# and add the PydanticPostprocessor to the postprocessors
scrape_crewmember = SchemaScraper(schema=CrewMember)
result = scrape_crewmember.scrape(
    "https://spaceghost.fandom.com/wiki/Zorak",
    extra_preprocessors=[CSS(".infobox")],
)
print(repr(result.data))
