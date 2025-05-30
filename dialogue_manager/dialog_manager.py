import os
from pathlib import Path
from dialogue_manager.state import State
from utils.asr import recognize_speech, record_audio
from user.log_utils import log_user_query
from user.get_location import get_location
from recommendation_engine.recommender import recommend_places
from recommendation_engine.prompt_builder import build_prompt, save_prompt
from recommendation_engine.prompt_builder import update_prompt_history, load_prompt
from information_retriever.retriever import retrieve_stations
from language_model.gpt4_driver_assistant import get_response
from preferences_database.update_preferences import add_history_entry
from recommendation_engine.evaluation import collect_user_feedback, evaluate_recommendations

PROMPT_DIR = Path("prompts")

class DialogueManager:
    def __init__(self, user_preferences):
        self.state = State.IDLE
        self.beginning = True
        self.next_proposal = False
        self.user_preferences = user_preferences
        self.user_query = ""
        self.response_user = ""
        self.stations = []
        self.exit = False
        self.recommendations = []
        self.ind = 0 #current recommendation index

    def handle_input(self):
        if self.state == State.IDLE:
            if self.beginning:
                self.state = State.ASK_QUESTION
                return "What would you like to know?"
            else:
                self.state = State.ASK_QUESTION

        elif self.state == State.ASK_QUESTION:
            audio_file = record_audio(duration=5)
            # Log the raw query
            self.user_query = recognize_speech(audio_file)
            print(f"👤 User : {self.user_query}")
            if not self.user_query:
                self.state == State.ASK_QUESTION
                return "Sorry, I couldn't record your audio. Please try again."
            else:
                log_user_query(self.user_query)

            self.state = State.RETRIEVE_STATIONS

        elif self.state == State.RETRIEVE_STATIONS:
            # Get the user's location
            coords = get_location()
            # Get the nearby stations
            self.stations = retrieve_stations(self.user_preferences, latlon=coords)
            if not self.stations:
                self.state = State.END
                return "No stations found nearby."
            
            self.state = State.GET_RECOMMENDATION
        
        elif self.state == State.GET_RECOMMENDATION:
            # Filter and rank the stations based on user preferences
            self.recommendations = recommend_places(self.user_preferences, self.stations)

            self.state = State.GENERATE_RESPONSE

        elif self.state == State.GENERATE_RESPONSE:
            response = ""
            if self.beginning:
                self.beginning = False
                top = self.recommendations[:3]
                # Create a prompt for the LLM
                # And save it to a file
                prompt = build_prompt(self.user_query, top)
                save_prompt(prompt)
                # Get the response from the LLM
                response = get_response(prompt)
                # Update the conversation history
                list_file = os.listdir(PROMPT_DIR)
                last_file = list_file[-1]
                update_prompt_history(last_file, response, who="assistant")

                self.state = State.WAIT_USER_RESPONSE

            else:
                if not self.next_proposal:
                    list_file = os.listdir(PROMPT_DIR)
                    last_file = list_file[-1]
                    prompt = load_prompt(last_file)
                    # Get the response from the LLM
                    response = get_response(prompt)
                    # Update the conversation history
                    update_prompt_history(last_file, response, who="assistant")

                    if "first" in self.response_user or "option one" in self.response_user or "number one" in self.response_user:
                        add_history_entry(self.recommendations[0]["name"], self.recommendations[0]["provider"], used=True)
                        self.state = State.SAVE_FEEDBACK

                    elif "second" in self.response_user or "option two" in self.response_user or "number two" in self.response_user:
                        add_history_entry(self.recommendations[1]["name"], self.recommendations[1]["provider"], used=True)
                        self.state = State.SAVE_FEEDBACK
                    
                    elif "third" in self.response_user or "option three" in self.response_user or "number three" in self.response_user:
                        add_history_entry(self.recommendations[2]["name"], self.recommendations[2]["provider"], used=True)
                        self.state = State.SAVE_FEEDBACK

                if self.next_proposal:
                    self.next_proposal = False
                    top = self.recommendations[self.ind:self.ind+3]
                    # Create a prompt for the LLM
                    prompt = build_prompt(self.user_query, top)
                    # Get the response from the LLM
                    response = get_response(prompt)
                    # Update the conversation history
                    list_file = os.listdir(PROMPT_DIR)
                    last_file = list_file[-1]
                    update_prompt_history(last_file, response, who="assistant")

                    self.state = State.WAIT_USER_RESPONSE

            return response
    
        elif self.state == State.WAIT_USER_RESPONSE:
            audio_file = record_audio(duration=5)
            
            # Log the raw query
            self.response_user = recognize_speech(audio_file)
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
            feedback = collect_user_feedback(self.recommendations)
            result = evaluate_recommendations(
                recommended=[r["name"] for r in self.recommendations],
                feedback=feedback
            )

            self.state = State.END

            return "Thanks for your feedback! It's been logged for future improvements."
        
        elif self.state == State.PROPOSE_NEXT:
            self.ind += 3
            if self.ind >= len(self.recommendations):
                self.state = State.END
                return "No more stations to suggest."
            
            self.state = State.GENERATE_RESPONSE

        elif self.state == State.END:
            mssg = input("Is there anything else I can help with?")
            if mssg.lower() in ["yes", "y", "sure", "go ahead"]:
                self.state = State.ASK_QUESTION
                self.beginning = True
                self.next_proposal = False
                self.user_query = ""
                self.response_user = ""
                self.stations = []
                self.recommendations = []
                self.ind = 0
            else:
                self.exit = True
                return "Thank you for using our service. Goodbye!"
            
