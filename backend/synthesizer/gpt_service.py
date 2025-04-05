import openai
import json
import os
import time

class GPTService:
    def __init__(self, api_key_path='api_key.txt', model='o3-mini'):
        """Initialize the GPT service with the API key and model."""
        self.available = False
        self.model = model
        
        try:
            # First check environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
            
            # If not in environment, try to load from file
            if not api_key:
                print("API key not found in environment, checking file...")
                # Load API key from file
                api_key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), api_key_path)
                try:
                    with open(api_key_file, 'r') as file:
                        api_key = file.read().strip()
                except FileNotFoundError:
                    print(f"Warning: API key file not found at {api_key_path}. GPT service will not be available.")
                    return
            
            # Set API key for the openai module (older style)
            if api_key:
                openai.api_key = api_key
                self.available = True
                print(f"GPT service initialized with model {model}")
            else:
                print("No API key found. GPT service will not be available.")
        except Exception as e:
            print(f"Error initializing GPT service: {str(e)}")

    def call_chatgpt(self, prompt, system_prompt=None):
        """Make a call to the ChatGPT API."""
        print("\n========== START call_chatgpt ==========")
        
        if not self.available:
            print("GPT service not available for API call")
            return '{"error": "GPT service not available"}'
            
        try:
            # Construct the message
            if system_prompt is None:
                msg = [{"role": "user", "content": prompt}]
                print("===== GPT QUERY =====")
                print(f"USER: {prompt}...")
                print(f"[Prompt length: {len(prompt)} chars]")
            else:
                msg = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
                print("===== GPT QUERY =====")
                print(f"SYSTEM: {system_prompt}")
                print(f"USER: {prompt}...")
                print(f"[Prompt length: {len(prompt)} chars]")
            
            print(f"Using model: {self.model}")
            print("Making API call to OpenAI...")
            start_time = time.time()
                
            # Make the API call
            try:
                completion = openai.ChatCompletion.create(
                    model=self.model,
                    messages=msg,
                )
                
                end_time = time.time()
                elapsed = end_time - start_time
                print(f"API call completed in {elapsed:.2f} seconds")
                
                # Get and print the response
                response = completion.choices[0].message.content
                print("===== GPT RESPONSE =====")
                print(f"[Response length: {len(response)} chars]")
                print(response)
                print("=========================")
                
                print("========== END call_chatgpt ==========\n")
                return response
                
            except Exception as api_error:
                print(f"API CALL ERROR: {str(api_error)}")
                print(f"Error type: {type(api_error).__name__}")
                import traceback
                traceback.print_exc()
                print("========== END call_chatgpt (with API error) ==========\n")
                return json.dumps({"error": f"API call error: {str(api_error)}"})
                
        except Exception as e:
            print(f"CRITICAL ERROR in call_chatgpt: {str(e)}")
            import traceback
            traceback.print_exc()
            print("========== END call_chatgpt (with error) ==========\n")
            return json.dumps({"error": str(e)})
        
    def is_available(self):
        """Check if the GPT service is available."""
        return self.available
        
    def classify_sentences(self, sentences, theme):
        """Classify multiple sentences as relevant to a theme and identify important words."""
        if not self.available:
            print("GPT service not available for classification")
            return {"error": "GPT service not available"}
        
        if not sentences or len(sentences) == 0:
            print("No sentences provided for classification")
            return {"error": "No sentences provided"}
            
        print(f"Classifying {len(sentences)} sentences for theme '{theme}'")
        
        sentences_formatted = "\n".join([f"- {ex}" for ex in sentences])
        
        prompt = f"""I have below sentences:
{sentences_formatted}

These sentences may be about this theme: "{theme}"

For each sentence, determine if it's relevant to the theme and identify the specific words that indicate relevance or non-relevance.

The output should provide for each sentence:
{{
"relevant": true/false,
"indexes": [list of word indexes that indicate relevance or non-relevance, starting from 0]
}}

For "indexes", include the 0-based indexes of ALL words that support your classification decision.
For example, if words at positions 2, 5, and 8 in the sentence are key to your decision, indexes would be [2, 5, 8].
It's important to include ALL relevant words, whether they indicate the sentence belongs to the theme or not.

Reply as JSON array only, with one object per sentence.
"""
        system_prompt = "You are a text classification expert focused on identifying key words that determine thematic relevance."
        
        try:
            print("Sending request to OpenAI API...")
            start_time = time.time()
            response = self.call_chatgpt(prompt, system_prompt)
            end_time = time.time()
            print(f"Received response from OpenAI API after {end_time - start_time:.2f} seconds")
            
            # Parse the response as JSON
            try:
                print("Parsing response as JSON...")
                parsed = json.loads(response)
                print(f"Successfully parsed response as JSON, received {len(parsed)} items")
                
                # Check if we have the right number of items
                if len(parsed) != len(sentences):
                    print(f"WARNING: Received {len(parsed)} results for {len(sentences)} sentences")
                
                # Validate the response format
                validated_results = []
                print("Validating results...")
                for i, item in enumerate(parsed):
                    if isinstance(item, dict) and "relevant" in item:
                        # Ensure indexes is a list of integers
                        if "indexes" not in item or not isinstance(item["indexes"], list):
                            print(f"Invalid 'indexes' for result {i}, setting to empty list")
                            item["indexes"] = []
                        else:
                            # Filter out any non-integer indexes
                            valid_indexes = [idx for idx in item["indexes"] if isinstance(idx, int)]
                            if len(valid_indexes) != len(item["indexes"]):
                                print(f"Filtered out invalid indexes for result {i}")
                            item["indexes"] = valid_indexes
                        
                        validated_results.append(item)
                        print(f"Result {i}: relevant={item['relevant']}, indexes={len(item['indexes'])}")
                    else:
                        # Add a placeholder for invalid results
                        print(f"Invalid result format at index {i}, using placeholder")
                        validated_results.append({
                            "relevant": False,
                            "indexes": [],
                            "explanation": "Invalid result format"
                        })
                    
                print(f"Returning {len(validated_results)} validated classification results")
                print("========== END classify_sentences ==========\n")
                return validated_results
                
            except json.JSONDecodeError as e:
                print(f"ERROR: JSON decode error: {e}")
                # Try to extract JSON from the response if there's additional text
                try:
                    # Look for text that could be JSON (between [ and ])
                    import re
                    print("Attempting to extract JSON from response...")
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        possible_json = json_match.group(0)
                        print(f"Found potential JSON: {possible_json[:100]}...")
                        parsed = json.loads(possible_json)
                        print(f"Successfully parsed extracted JSON with {len(parsed)} items")
                        print("========== END classify_sentences (with JSON extraction) ==========\n")
                        return parsed
                except Exception as inner_e:
                    print(f"ERROR extracting JSON: {inner_e}")
                
                # Fallback if response is not valid JSON
                print(f"Failed to parse response as JSON. First 200 chars: {response}...")
                print("========== END classify_sentences (with error) ==========\n")
                return {"error": "Invalid response format", "raw_response": response}
                
        except Exception as e:
            print(f"CRITICAL ERROR in classify_sentences: {e}")
            import traceback
            traceback.print_exc()
            print("========== END classify_sentences (with error) ==========\n")
            return {"error": f"Classification error: {str(e)}"} 