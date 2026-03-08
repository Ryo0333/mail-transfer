from pydantic import BaseModel, StrictStr


class Mail(BaseModel):
    subject: StrictStr
    from_: StrictStr
    body: StrictStr
