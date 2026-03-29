from pydantic import BaseModel, StrictStr


class Mail(BaseModel):
    message_id: StrictStr
    subject: StrictStr
    sender: StrictStr
    body: StrictStr
