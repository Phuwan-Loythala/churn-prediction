from pydantic import BaseModel

class CustomerData(BaseModel):
    Support_Calls: int
    Contract_Length: str
    Total_Spend: float
    Payment_Delay: int
    Last_Interaction: int
