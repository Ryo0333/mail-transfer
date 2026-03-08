from pydantic import BaseModel, StrictStr


class Mail(BaseModel):
    subject: StrictStr
    sender: StrictStr
    body: StrictStr
