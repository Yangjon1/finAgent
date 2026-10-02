from pydantic import BaseModel, Field


class ExpenseAgentStartRequest(BaseModel):
    report_id: str


class ExpenseAgentResumeRequest(BaseModel):
    decision: str = Field(pattern=r"^(APPROVE|REJECT|RETURN)$")
