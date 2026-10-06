from fastapi import FastAPI, HTTPException #these ones are for making the api and handling the errors
import joblib #this one is for loading the model
from pydantic import BaseModel, Field # BaseMOdel is for data validation and Field is for adding extra details to our data fields
import numpy as np 


app = FastAPI( #just creating the app instance
    title = 'Kopa Score Prediction API',
    description = 'API for digtal micro-lending default risk',
    version = '1.0.0'
)

model = joblib.load("lightgbm_model.joblib") #just like the 'Pickle' library that saves the model 
core_features = joblib.load("core_features.joblib") #this one loads the core features that will be used to make predictions


DECISION_THRESHOLD = 0.4 #setting the threshold for the model predictions

#define the data schema -- basically ensuring the data is in the right format before it even goes to the model --> Pydantic


class RawBorrowerData(BaseModel): #defining the borrower application data -- i used RawBorrowerData cause the data is raw and it has not been processed yet 
    requested_loan_amount: float = Field(
        ..., #the ... means that the data is required
        example=10000.0,
        description="The amount of loan the borrower is requesting"
    )

    monthly_inflow: float = Field(
        ...,
        example=40000,
        description="Total monthly income of the borrower"
    )

    monthly_outflow: float = Field(
        ...,
        example = 22000,
        description="Total monthly expenses of the borrower"
    )

    inflow_volatility: float = Field(
        ...,
        example = 0.15,
        description="Measure of income fluctuation"
    )

    prior_defaults: int = Field(
        ...,
        example = 0,
        description="Number of past loan defaults"
    )


def calculate_kopascore(default_probability: float) -> int: #define the function that will calculate the kopa score
    score = 850 - (default_probability * 550) #setting the formula for the kopa score (850 is the max score and 300 is the minimum)
    return int(np.clip(score, 300,850)) #this one basically ensures that the score stays within the 300-850 range


@app.get("/") #this one basically just says hey when someone opens the api in their browser

def root():
    return {
        "message": "Welcome to the Kopa Score Prediction API",
        "status":"active",
        "version":"1.0.0"
        }


@app.post("/predict")
#this one basically tells the api to expect the data in the form of the BorrowerApplication schema defined above
def predict_credit_risk(raw_data: RawBorrowerData): 
    try:
        if raw_data.requested_loan_amount <=0 or raw_data.monthly_inflow <=0:
            raise HTTPException(
                status_code=400,
                detail="Loan amount and monthly income must be positive"
            )
        
        #feature engineering --this is where we create new features from the raw data, just like we did in the notebook
        loan_to_income_ratio = raw_data.requested_loan_amount / raw_data.monthly_inflow
        net_cashflow = raw_data.monthly_inflow - raw_data.monthly_outflow
        net_cashflow_ratio = net_cashflow / raw_data.monthly_inflow

        calculated_features = {
            "loan_to_income_ratio": loan_to_income_ratio,
            "net_cashflow_ratio": net_cashflow_ratio,
            "inflow_volatility": raw_data.inflow_volatility,
            "prior_defaults": raw_data.prior_defaults
        }

        #Converting the features into a format that the model can understand (A 2D ARRAY)
        ordered_features = [calculated_features[feature] for feature in core_features]
        features_array = np.array([ordered_features])

        #making the prediction
        default_probability = float(model.predict_proba(features_array)[:,1][0])

        kopascore = calculate_kopascore(default_probability) #calculating the kopa score

        if default_probability <= DECISION_THRESHOLD:
            decision = "APPROVE"
            risk_category = "Low"
            recommendation = "Applicant has a low probability of default, proceed with loan disbursement"
        else:
            decision = "REJECT"
            risk_category = "High"
            recommendation = "Applicant has a high probability of default, reject loan application"

        return {
            "kopascore": kopascore,
            "default_probability": default_probability,
            "risk_category": risk_category,
            "decision": decision,
            "recommendation": recommendation,
            "engineered_metrics": {
                "loan_to_income_ratio": loan_to_income_ratio,
                "net_cashflow_ratio": net_cashflow_ratio,
                "calculated_net_cashflow_kes": net_cashflow,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )
    



