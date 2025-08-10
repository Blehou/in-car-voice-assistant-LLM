import os
import time
from pathlib import Path
from joblib import load

from dialogue_manager.state import State

from utils.asr import record_audio, recognize_speech_fast
from utils.asr import recognize_speech
from user.log_utils import log_user_query
from user.get_location import get_location

from recommendation_engine.recommender import recommend_places
from recommendation_engine.prompt_builder import build_prompt, save_prompt
from recommendation_engine.prompt_builder import update_prompt_history, load_prompt
from recommendation_engine.evaluation import collect_user_feedback, evaluate_recommendations
from recommendation_engine.evaluation import is_empty_log_feedback
from recommendation_engine.evaluation import compute_BERTScore, compute_ROUGE_L

from information_retriever.retriever import retrieve_stations
from information_retriever.retriever import retrieve_restaurants
from information_retriever.retriever import  retrieve_hobby_activity

from language_model.gpt4_driver_assistant import get_response
from language_model.llama_driver_assistant import get_llama_response
from language_model.gemini_driver_assistant import get_gemini_response
from language_model.deepseek_driver_assistant import get_deepseek_response
from language_model.claude_driver_assistant import get_claude_response

from intent_classifier.classifier2 import get_intent

from preferences_database.update_preferences import add_history_entry


PROMPT_DIR = Path("prompts")
# Path to the saved model
MODEL_PATH = Path("intent_classifier/Models/intent_classifier.pkl")


class DialogueManager:
    def __init__(self, user_preferences:dict):
        """
        Initialize the DialogueManager with the user's preferences.

        Args:
            user_preferences (dict): A dictionary containing the user's settings,
                including fuel type, preferred providers, max detour distance,
                power requirements, and history.
        """
        self.state = State.IDLE

        self.beginning = True
        self.next_proposal = False
        self.exit = False

        self.user_preferences = user_preferences

        self.user_query = ""
        self.response_user = ""

        self.model = load(MODEL_PATH)
        self.intent = ""
        self.keyword = ""
        self.feedback = None

        self.nearby_POIs = []
        self.recommendations = []
        self.selected_recommendation = None

        self.timeToRecommendation = 0
        # timestamp for the start of 
        # the current recommendation
        self.start_time = 0
        # timestamp for the end of 
        # the current recommendation
        self.end_time = 0
        # current recommendation index
        self.ind = 0 
        self.bert_score = 0.0
        self.rouge_l_score = 0.0

    def handle_input(self):
        """
        Handle the current step of the dialogue based on the internal state.

        This function manages the full dialogue loop, transitioning between
        states such as asking a question, retrieving point of interest, generating
        recommendations, waiting for user feedback, and saving evaluation data.

        Returns:
            str: The assistant's spoken or printed response at the current step,
                or None if no output is needed.
        """

        if self.state == State.IDLE:
            if self.beginning:
                self.start_time = time.time()
                self.state = State.ASK_QUESTION
                return "What would you like to know?"
            else:
                self.start_time = time.time()
                self.state = State.ASK_QUESTION

        elif self.state == State.ASK_QUESTION:
            audio_file = record_audio(duration=3)

            # Log the raw query
            ### self.user_query = recognize_speech(audio_file)
            self.user_query = recognize_speech_fast(audio_file)
            print(f"👤 User : {self.user_query}")

            if not self.user_query:
                self.state == State.ASK_QUESTION
                return "Sorry, I couldn't record your audio. Please try again."
            
            else:
                log_user_query(self.user_query)

            self.state = State.INTENT_CLASSIFIER

        elif self.state == State.INTENT_CLASSIFIER:
            # Predict the intent of the user's query
            print("Predicting intent...")
            # self.intent = self.model.predict([self.user_query])[0]
            keywords = get_intent(self.user_query)
            self.intent = keywords[0] 
            self.keyword = keywords
            print(f"Predicted intent: {self.intent}\n")

            self.state = State.RETRIEVE_POIs

        elif self.state == State.RETRIEVE_POIs:
            question = input("Do you want to use your current location? (yes/no): ").strip().lower()

            if question in ["yes", "y"]:
                # Get the user's location
                coords = get_location()

                if self.intent == "stations":
                    # Get the nearby stations
                    self.nearby_POIs = retrieve_stations(self.user_preferences, latlon=coords)
                elif self.intent == "restaurants":
                    # Get the nearby restaurants
                    self.nearby_POIs = retrieve_restaurants(self.user_preferences, keywords=self.keyword, latlon=coords)
                elif self.intent == "hobbies":
                    # Get the nearby hobby activities
                    self.nearby_POIs = retrieve_hobby_activity(self.user_preferences, keyword=self.keyword, latlon=coords)

            elif question in ["no", "n"]:
                # Ask the user for their location address
                address = input("Please provide your location address: ")

                if self.intent == "stations":
                    # Get the nearby stations based on the provided address
                    self.nearby_POIs = retrieve_stations(self.user_preferences, location_input=address)
                elif self.intent == "restaurants":
                    # Get the nearby restaurants based on the provided address
                    self.nearby_POIs = retrieve_restaurants(self.user_preferences, keywords=self.keyword, location_input=address)
                elif self.intent == "hobbies":
                    # Get the nearby hobby activities based on the provided address
                    self.nearby_POIs = retrieve_hobby_activity(self.user_preferences, keyword=self.keyword, location_input=address)

            if not self.nearby_POIs:
                self.state = State.END
                return "No points of interest found nearby."

            self.state = State.GET_RECOMMENDATION
        
        elif self.state == State.GET_RECOMMENDATION:
            self.feedback = is_empty_log_feedback()
            # Filter and rank the stations based on user preferences
            self.recommendations = recommend_places(self.user_preferences, self.nearby_POIs, self.intent, self.feedback)
            
            if not self.recommendations:
                self.state = State.END
                return "No recommendations available based on your preferences."

            self.state = State.GENERATE_RESPONSE

        elif self.state == State.GENERATE_RESPONSE:
            response = ""
            
            if self.beginning:
                self.beginning = False
                top = self.recommendations[:3]

                # Create a prompt for the LLM
                # And save it to a file
                prompt = build_prompt(self.user_query, top, self.intent)
                save_prompt(prompt)

                # Get the response from the LLM
                start = time.time()

                # GPT4
                response = get_response(prompt)

                # Llama
                ## response = get_llama_response(prompt)

                # Gemini
                ## response = get_gemini_response(prompt)

                # Deepseek
                ## response = get_deepseek_response(prompt)
                
                # Claude
                ## response = get_claude_response(prompt)

                end = time.time()
                print(f"Response time: {end - start:.2f} seconds")

                # Update the conversation history
                list_file = os.listdir(PROMPT_DIR)
                last_file = list_file[-1]
                update_prompt_history(last_file, response, who="assistant")

                # Calcul de BERTScore
                self.bert_score = compute_BERTScore(response)
                
                # Calcul de ROUGE-L
                self.rouge_l_score = compute_ROUGE_L(response)

                self.state = State.WAIT_USER_RESPONSE

            else:
                if not self.next_proposal:
                    # load prompt
                    list_file = os.listdir(PROMPT_DIR)
                    last_file = list_file[-1]
                    prompt = load_prompt(last_file)

                    # Get the response from the LLM
                    # GPT4
                    response = get_response(prompt)

                    # Llama
                    ## response = get_llama_response(prompt)

                    # Gemini
                    ## response = get_gemini_response(prompt)

                    # Deepseek
                    ## response = get_deepseek_response(prompt)
                
                    # Claude
                    ## response = get_claude_response(prompt)

                    # Update the conversation history
                    update_prompt_history(last_file, response, who="assistant")

                    if any(phrase in self.response_user for phrase in ["first", "option one", "number one", "let's go", "let's start", "let's do it"]):
                        self.end_time = time.time()
                        self.timeToRecommendation = self.end_time - self.start_time

                        if self.intent == "stations":
                            add_history_entry(self.recommendations[0]["name"], self.recommendations[0]["provider"], self.intent, used=True)
                        elif self.intent in ["restaurants", "hobbies"]:
                            add_history_entry(self.recommendations[0]["address"], self.recommendations[0]["name"], self.intent, used=True)

                        print(f"Time taken to get recommendation: {self.timeToRecommendation:.2f} seconds")

                        self.selected_recommendation = self.recommendations[0]

                        self.state = State.SAVE_FEEDBACK

                    elif "second" in self.response_user or "option two" in self.response_user or "number two" in self.response_user:
                        self.end_time = time.time()
                        self.timeToRecommendation = self.end_time - self.start_time

                        if self.intent == "stations":
                            add_history_entry(self.recommendations[1]["name"], self.recommendations[1]["provider"], self.intent, used=True)
                        elif self.intent in ["restaurants", "hobbies"]:
                            add_history_entry(self.recommendations[1]["address"], self.recommendations[1]["name"], self.intent, used=True)

                        print(f"Time taken to get recommendation: {self.timeToRecommendation:.2f} seconds")

                        self.selected_recommendation = self.recommendations[1]

                        self.state = State.SAVE_FEEDBACK
                    
                    elif "third" in self.response_user or "option three" in self.response_user or "number three" in self.response_user:
                        self.end_time = time.time()
                        self.timeToRecommendation = self.end_time - self.start_time

                        if self.intent == "stations":
                            add_history_entry(self.recommendations[2]["name"], self.recommendations[2]["provider"], self.intent, used=True)
                        elif self.intent in ["restaurants", "hobbies"]:
                            add_history_entry(self.recommendations[2]["address"], self.recommendations[2]["name"], self.intent, used=True)

                        print(f"Time taken to get recommendation: {self.timeToRecommendation:.2f} seconds")

                        self.selected_recommendation = self.recommendations[2]
                        
                        self.state = State.SAVE_FEEDBACK
                    else:
                        self.state = State.WAIT_USER_RESPONSE
                        

                if self.next_proposal:
                    self.next_proposal = False
                    top = self.recommendations[self.ind:self.ind+3]

                    # Create a prompt for the LLM
                    prompt = build_prompt(self.user_query, top, self.intent)

                    # Get the response from the LLM
                    # GPT4
                    response = get_response(prompt)

                    # Llama
                    ## response = get_llama_response(prompt)

                    # Gemini
                    ## response = get_gemini_response(prompt)

                    # Deepseek
                    ## response = get_deepseek_response(prompt)
                    
                    # Claude
                    ## response = get_claude_response(prompt)

                    # Update the conversation history
                    list_file = os.listdir(PROMPT_DIR)
                    last_file = list_file[-1]
                    update_prompt_history(last_file, response, who="assistant")

                    self.state = State.WAIT_USER_RESPONSE
            
            return response
    
        elif self.state == State.WAIT_USER_RESPONSE:
            audio_file = record_audio(duration=3)
            
            # Log the raw query
            ### self.response_user = recognize_speech(audio_file)
            self.response_user = recognize_speech_fast(audio_file)
            print(f"👤 User : {self.response_user}")

            if not self.response_user:
                self.state == State.WAIT_USER_RESPONSE
                return "Sorry, I couldn't record your audio. Please try again."
            
            # Update the conversation history
            list_file = os.listdir(PROMPT_DIR)
            last_file = list_file[-1]
            update_prompt_history(last_file, self.response_user, who="user")

            if any(word in self.response_user for word in ["none", "don’t like", "another", "other"]):
                self.next_proposal = True
                self.state = State.PROPOSE_NEXT
                return "Okay, I’ll search for alternative recommendations."

            self.state = State.GENERATE_RESPONSE
        
        elif self.state == State.SAVE_FEEDBACK:
            print("\nLet's evaluate your experience.")
            feedback = collect_user_feedback(self.selected_recommendation)
            result = evaluate_recommendations(
                recommended=[self.selected_recommendation["name"]],
                feedback=feedback, 
                BERTScore=self.bert_score,
                RougeScore=self.rouge_l_score,
            )

            self.state = State.END

            return "Thanks for your feedback! It's been logged for future improvements."
        
        elif self.state == State.PROPOSE_NEXT:
            self.ind += 3
            if self.ind >= len(self.recommendations):
                self.state = State.END
                return "No more recommendations to suggest."

            self.state = State.GENERATE_RESPONSE

        elif self.state == State.END:
            mssg = input("Is there anything else I can help with?")
            if mssg.lower() in ["yes", "y", "sure", "go ahead"]:
                self.state = State.ASK_QUESTION
                self.beginning = True
                self.next_proposal = False
                self.user_query = ""
                self.response_user = ""
                self.nearby_POIs = []
                self.intent = ""
                self.feedback = None
                self.selected_recommendation = None
                self.recommendations = []
                self.start_time = 0
                self.end_time = 0
                self.ind = 0
            elif mssg.lower() in ["no", "n", "exit", "quit", "stop"]:
                self.exit = True
                return "Thank you for using our service. Goodbye!"
            else:
                print("Invalid response. Please answer with 'yes' or 'no'.")
                self.state == State.END
