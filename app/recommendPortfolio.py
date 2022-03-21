### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function

In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.

1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.

2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.

3. Complete the `recommend_portfolio()` function by adding these validation rules:

    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.

4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:

    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"

> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!

5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.

6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.

7. Build your bot, and test it with valid and invalid data for the slots.

"""

def make_validation_struct(is_valid, violated_slot, message_content):
    """
    creates validation message
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


def validate_slot_data(age, investment_amount):
    """
    Validates the slot data -- age, investment_amount
    """
    # The `age` should be greater than zero and less than 65.
    if age is not None:
        age = parse_int(age)

        # invalid age?
        if not ((age > 0) and (age < 65)):
            return build_validation_result(
                False,
                "age",
                "Age must be greater than 0 and less than 65."
            )

    # investment_amount defined and valid?
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)

        # valid investment_amount - should be equal to or greater than 5000.
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investment_amount",
                "Investment amount must be greater than or equal to 5000."
            )

    # all slots are valid return true validation
    return build_validation_result(True, None, None)


def get_investment_recommendation(risk_level):
    """
    returns investement recommendation string based on risk level
    """
    risk = str(risk_level).lower()

    recommendations = {
        'none' : '100% bonds (AGG), 0% equities (SPY)',
        'low' : '60% bonds (AGG), 40% equities (SPY)',
        'medium' : '40% bonds (AGG), 60% equities (SPY)',
        'high' : '20% bonds (AGG), 80% equities (SPY)'
    }

    return recommendations.get(risk)


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    # get some key slot data
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]

    # note the source
    source = intent_request["invocationSource"]
    
    if source == "DialogCodeHook":
        # get all the slots
        slots = get_slots(intent_request)

        #check validity of the key slots -- age, investment_risk
        validation_dict = validate_slot_data(age, investment_amount)


        # invalid data will elict re-prompt
        if not validation_dict["isValid"]:
            slots[validation_dict["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_dict["violatedSlot"],
                validation_dict["message"],
            )
        
        # grab current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        # when valid, return delegate to Lex bot
        return delegate(output_session_attributes, get_slots(intent_request))

    investment_recommendation_text = get_investment_recommendation(risk_level)

    return close(intent_request["sessionAttributes"], 
    "Fulfilled",
        {
            "contentType": "PlainText",
            "content": investment_recommendation_text }
            )



### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
