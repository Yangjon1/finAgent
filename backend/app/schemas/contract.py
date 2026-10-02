from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    contract_no: str = Field(min_length=1, max_length=128)
    counterparty_id: str | None = None
    content: str = Field(min_length=1)
    file_id: str | None = None


class ContractAnalyzeRequest(BaseModel):
    contract_id: str


class ContractResumeRequest(BaseModel):
    decision: str = Field(pattern=r"^(APPROVE|REJECT|RETURN)$")
