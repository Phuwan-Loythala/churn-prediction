from pydantic import BaseModel

class CustomerData(BaseModel):
    credit_score: int
    geography: int
    gender: int
    age: int
    tenure: int
    balance: float
    num_of_products: int
    has_credit_card: int
    is_active_member: int
    estimated_salary: float