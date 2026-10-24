from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import NonEmptyStr

REQUIRED_LOCATION = "luweero"


class ContractCreate(BaseModel):
    engineer_name: NonEmptyStr
    client_name: NonEmptyStr
    project_location: NonEmptyStr
    milestone_title: NonEmptyStr
    milestone_budget_ugx: int = Field(gt=0)

    @field_validator("project_location")
    @classmethod
    def location_must_be_in_luweero(cls, value: str) -> str:
        if REQUIRED_LOCATION not in value.lower():
            raise ValueError(
                "project_location must be within Luweero district "
                "(e.g. 'Luweero Town Council')"
            )
        return value


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    engineer_name: str
    client_name: str
    project_location: str
    milestone_title: str
    milestone_budget_ugx: int
    status: str
    created_at: datetime
    updated_at: datetime
