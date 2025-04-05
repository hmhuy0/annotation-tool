from fastapi import FastAPI, Cookie, Request, Response, Header
from synthesizer.api_helper import *
from api.schemas.Theme import *
from api.schemas.Labeling import *
from synthesizer.penality_based_threaded import Synthesizer 
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ProcessPoolExecutor
import asyncio
import time
from pydantic import BaseModel
from typing import List
from fastapi import Request
from fastapi.responses import JSONResponse

import pandas as pd

import random
import torch
import numpy as np

torch.multiprocessing.set_start_method('spawn', force=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
# torch.cuda.manual_seed_all(SEED)

executor = ProcessPoolExecutor()
loop = asyncio.get_event_loop()


app = FastAPI()

user_to_apiHelper = {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




class LablingModel(BaseModel):
    theme: str
    elementId: str = None
    phrase: str = None
    positive: int = 1
    pattern: str = None



class Item(BaseModel):
    depth: int
    rewardThreshold: float
    penalityThreshold: float
    featureSelector: int
class BulkLabel(BaseModel):
    ids: List[str]
    label: str
    positive: str
class PatternsSplitThemeItem(BaseModel):
    patterns: List[str]
    new_theme_name: str
    theme: str

class GPTConfigItem(BaseModel):
    model: str = "o3-mini"
    use_gpt: bool = True

@app.get("/")
async def home():
    return {"status":"Running"}


@app.get("/bert_annotation")
async def bert_annotation(request:Request, batch:int = None, batch_size:int = None):
    print("\n========== BERT_ANNOTATION ENDPOINT START ==========")
    print(f"Called with batch={batch}, batch_size={batch_size}")
    
    user = request.headers.get('annotuser')
    print(f"User: {user}")
    
    if(user=="null" or user==None):
        print("Unauthorized user attempt")
        print("========== BERT_ANNOTATION ENDPOINT END (Unauthorized) ==========\n")
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    
    try:
        print(f"Processing request for user {user}")
        # Get the API helper for this user
        api_helper = user_to_apiHelper[user]
        
        # Check if theme is selected
        theme = api_helper.get_selected_theme()
        print(f"Selected theme: {theme}")
        
        # Use GPT directly for annotation
        print(f"Starting executor.submit for get_gpt_annotation")
        print(f"Parameters: batch={batch}, batch_size={batch_size}")
        
        start_time = time.time()
        results = await loop.run_in_executor(executor, api_helper.get_gpt_annotation, batch, batch_size)
        end_time = time.time()
        
        print(f"get_gpt_annotation completed in {end_time - start_time:.2f} seconds")
        
        # Check results
        if isinstance(results, dict):
            status = results.get("status_code", 200)
            message = results.get("message", "OK")
            scores_count = len(results.get("scores", {}))
            explanation_count = len(results.get("explanation", {}).get("GPT", {}))
            print(f"Results: status={status}, message={message}, scores={scores_count}, explanations={explanation_count}")
        else:
            print(f"Unexpected result type: {type(results)}")
        
        print("========== BERT_ANNOTATION ENDPOINT END (Success) ==========\n")
        return results
    except Exception as e:
        print(f"ERROR in bert_annotation endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        print("========== BERT_ANNOTATION ENDPOINT END (Error) ==========\n")
        return {
            "status_code": 500,
            "message": f"Error processing bert_annotation: {str(e)}",
            "scores": {},
            "explanation": {}
        }

@app.get("/restore_session/{user}")
async def restore_session(user: str):
    return {}


@app.get("/create_session/{user}")
async def create_session(user: str):
    print("The user in create session is ", user)
    if(user not in user_to_apiHelper):
        user_to_apiHelper[user] = APIHelper(user=user)
    return "Done"

threadpool = {}

###v1 endpoints
@app.get("/dataset")
async def get_labeled_examples(request: Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    
    if(user not in user_to_apiHelper):
        user_to_apiHelper[user] = APIHelper(user=user)
    # print("coookiieee", user)
    return user_to_apiHelper[user].get_labeled_dataset()



@app.post("/phrase")
async def label_element_by_phrase(request: Request, body: LablingModel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results = user_to_apiHelper[user].label_by_phrase(body.phrase, body.theme, body.positive, body.elementId)
    return results

@app.post("/clear")
async def clear_labeling(request:Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    return user_to_apiHelper[user].clear_label()

@app.get("/combinedpatterns")
async def combinedpatterns(request:Request, batch:int = None, batch_size:int = None):
    print("\n========== COMBINEDPATTERNS ENDPOINT START ==========")
    print(f"Called with batch={batch}, batch_size={batch_size}")
    
    user = request.headers.get('annotuser')
    print(f"User: {user}")
    
    if(user=="null" or user==None):
        print("Unauthorized user attempt")
        print("========== COMBINEDPATTERNS ENDPOINT END (Unauthorized) ==========\n")
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    
    try:
        print(f"Processing request for user {user}")
        # Get the API helper for this user
        api_helper = user_to_apiHelper[user]
        
        # Check if theme is selected
        theme = api_helper.get_selected_theme()
        print(f"Selected theme: {theme}")
        
        # Use GPT directly for annotation instead of pattern synthesis
        print(f"Starting executor.submit for get_gpt_annotation")
        print(f"Parameters: batch={batch}, batch_size={batch_size}")
        
        start_time = time.time()
        results = await loop.run_in_executor(executor, api_helper.get_gpt_annotation, batch, batch_size)
        end_time = time.time()
        
        print(f"get_gpt_annotation completed in {end_time - start_time:.2f} seconds")
        
        # Save results
        user_to_apiHelper[user].results = results
        
        # Check results
        if isinstance(results, dict):
            status = results.get("status_code", 200)
            message = results.get("message", "OK")
            scores_count = len(results.get("scores", {}))
            explanation_count = len(results.get("explanation", {}).get("GPT", {}))
            print(f"Results: status={status}, message={message}, scores={scores_count}, explanations={explanation_count}")
        else:
            print(f"Unexpected result type: {type(results)}")
        
        print("========== COMBINEDPATTERNS ENDPOINT END (Success) ==========\n")
        return results
    except Exception as e:
        print(f"ERROR in combinedpatterns endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        print("========== COMBINEDPATTERNS ENDPOINT END (Error) ==========\n")
        return {
            "status_code": 500,
            "message": f"Error processing combinedpatterns: {str(e)}",
            "scores": {},
            "explanation": {}
        }

@app.get("/test/{iteration}/{annotation}")
async def test(iteration:int, annotation: int, body:Item):
    print(body)
    start =  time.time()
    results = user_to_apiHelper['simret'].run_test(iteration, annotation, depth= body.depth, rewardThreshold=body.rewardThreshold, penalityThreshold=body.penalityThreshold)
    end = time.time()
    print(results)
    results[0]['time'] = end-start

    return results

@app.get("/themes")
async def get_themes(request:Request):
    user = request.headers.get("annotuser")
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    return user_to_apiHelper[user].all_themes

@app.post("/add_theme")
async def add_theme(request:Request, body:ThemeName):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    return user_to_apiHelper[user].add_theme(body.theme)


@app.post("/delete_theme")
async def delete_theme(request:Request, body:ThemeName):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    return user_to_apiHelper[user].delete_theme(body.theme)

@app.get("/selected_theme")
async def get_selected_theme(request:Request):
    user = request.headers.get("annotuser")
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    if(user_to_apiHelper[user].get_selected_theme() in user_to_apiHelper[user].all_themes):
        return user_to_apiHelper[user].get_selected_theme()
    else:
        return None


@app.post("/set_theme")
async def set_theme(request: Request, body:ThemeName):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    return (body.theme,user_to_apiHelper[user].set_theme(body.theme))

@app.get("/related_examples/{id}")
async def get_related_examples(request:Request, id:str):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # Since we're not using patterns, just return empty results
    # In a real implementation, you could query GPT directly for similar examples
    return [], {}

@app.get("/explain/{pattern}")
async def explain_pattern(request: Request, pattern:str):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # This now directly explains the relationship between text and theme without patterns
    api_helper = user_to_apiHelper[user]
    results = await loop.run_in_executor(executor, api_helper.explain_pattern, pattern)
    return results

def main():
    synthh = Synthesizer(positive_examples = "examples/price_big", negative_examples = "examples/not_price_big")
    print(synthh.find_patters(outfile="small_thresh"))
# main() pid 31616

######################################################################################################################
@app.post("/delete_label")
async def delete_label(request:Request, body: LablingModel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].delete_label, body.elementId, body.theme)
    res = await future1
    return res


@app.post("/merge_themes")
async def merge_themes(request:Request, body:MergeThemeItem):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].merge_themes, body.theme1, body.theme2, body.new_theme)
    res = await future1
    return res


@app.post("/split_theme")
async def split_themes(request:Request, body: SplitThemeItem):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].split_theme, body.theme, body.group1, body.group2)
    res = await future1
    return res

@app.post("/split_theme_by_pattern")
async def split_themes_by_pattern( request:Request, body: PatternsSplitThemeItem):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # Patterns are not used in this version
    return {
        "status_code": 200,
        "message": "Patterns are not used in this version. Cannot split by pattern."
    }

@app.post("/rename_theme")
async def split_themes_by_pattern(request:Request, body: RenameTheme):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].rename_theme, body.theme, body.new_name)
    res = await future1
    return res


@app.post("/label")
async def label_example(request:Request, body: LablingModel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].label_element, body.elementId, body.theme, body.positive)
    res = await future1
    return res

@app.post("/bulk_label")
async def bulk_label_example(request:Request, body: BulkLabel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    future1 = loop.run_in_executor(None, user_to_apiHelper[user].bulk_label_element, body.ids, body.label, body.positive)
    res = await future1
    return res

@app.post("/labeled_data")
async def labeled_data(request:Request, body: ThemeName):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results = await loop.run_in_executor(executor, user_to_apiHelper[user].get_user_labels, body.theme)
    return results



@app.get("/patterns")
async def patterns(request: Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }

    # Skip pattern synthesis entirely - just return empty patterns
    # No need to call GPT for patterns since we're not using them
    return {"patterns": [], "scores": {}}

@app.get("/annotations")
async def annotations(request:Request, refresh:bool = False, batch:int = None, batch_size:int = None):
    print("\n========== ANNOTATIONS ENDPOINT START ==========")
    print(f"Called with batch={batch} (type: {type(batch)}), batch_size={batch_size}, refresh={refresh}")
    print(f"Request query params: {dict(request.query_params)}")
    print(f"Request headers: {dict(request.headers.items())}")
    
    # Extract batch parameter directly from query params if needed
    query_params = dict(request.query_params)
    batch_param = query_params.get('batch')
    if batch_param:
        try:
            # Ensure batch is an integer
            batch = int(batch_param)
            print(f"Converted batch parameter from query string: {batch}")
        except ValueError:
            print(f"Failed to convert batch parameter to int: {batch_param}")
    
    # Special handling for batch=1 for debugging
    if batch == 1 or batch_param == '1':
        print("!!! SPECIAL DEBUGGING FOR BATCH 1 !!!")
        print("This is the batch we're having issues with")
        print(f"Request info: {request}")
        try:
            print("Request body:", await request.body())
        except:
            print("Could not read request body")
    
    # Get user from headers
    user = request.headers.get('annotuser')
    print(f"User: {user}")
    
    if(user=="null" or user==None):
        print("Unauthorized user attempt")
        print("========== ANNOTATIONS ENDPOINT END (Unauthorized) ==========\n")
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    
    print(f"Processing request for user {user}")
    try:
        # Check if user exists in dict
        if user not in user_to_apiHelper:
            print(f"Creating new APIHelper for user {user}")
            user_to_apiHelper[user] = APIHelper(user=user)
        
        # Get the API helper for this user
        api_helper = user_to_apiHelper[user]
        
        # Check if theme is selected
        theme = api_helper.get_selected_theme()
        print(f"Selected theme: {theme}")
        
        # Print info about executor
        print(f"Using executor: {type(executor).__name__}")
        print(f"Active worker count: {executor._max_workers}")
        
        # Special handling for batch=1 for debugging
        if batch == 1 or batch_param == '1':
            print("!!! SPECIAL DEBUG FOR BATCH 1 - About to call get_gpt_annotation !!!")
        
        # Directly use GPT for annotation without pattern model
        print(f"Starting executor.submit for get_gpt_annotation")
        print(f"Parameters: batch={batch}, batch_size={batch_size}")
        
        start_time = time.time()
        # Run the function in the executor
        results = await loop.run_in_executor(executor, api_helper.get_gpt_annotation, batch, batch_size)
        end_time = time.time()
        
        print(f"get_gpt_annotation completed in {end_time - start_time:.2f} seconds")
        
        # Check results
        if isinstance(results, dict):
            print("========== GPT RESPONSE ==========")
            print(results)
            print("========== GPT RESPONSE END ==========")
            
            status = results.get("status_code", 200)
            message = results.get("message", "OK")
            scores_count = len(results.get("scores", {}))
            explanation_count = len(results.get("explanation", {}).get("GPT", {}))
            print(f"Results: status={status}, message={message}, scores={scores_count}, explanations={explanation_count}")
        else:
            print(f"Unexpected result type: {type(results)}")
        
        print("========== ANNOTATIONS ENDPOINT END (Success) ==========\n")
        return results
    except Exception as e:
        print(f"ERROR in annotations endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        print("========== ANNOTATIONS ENDPOINT END (Error) ==========\n")
        return {
            "status_code": 500,
            "message": f"Error processing annotations: {str(e)}",
            "scores": {},
            "explanation": {}
        }

@app.get("/delete_softmatch/{pattern}/{softmatch}")
async def delete_softmatch(request:Request, pattern:str, softmatch:str):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results = await loop.run_in_executor(executor, user_to_apiHelper[user].delete_softmatch, pattern, softmatch)
    return results

@app.get("/delete_softmatch_globally/{pivot_word}/{similar_word}")
async def delete_softmatch_globally_end(request:Request, pivot_word:str, similar_word:str):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results = user_to_apiHelper[user].delete_softmatch_globally(pivot_word, similar_word)
    return results

@app.get("/toggle_binary_mode/{binary_mode}")
async def toggle_binary_mode(request:Request, binary_mode:int):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results =  user_to_apiHelper[user].toggle_binary_mode(binary_mode)
    return results



@app.post("/delete_pattern")
async def delete_pattern(request:Request, body: LablingModel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # No patterns to delete in the new implementation
    return {"status_code": 200, "message": "Patterns are not used in this version"}


@app.post("/pin_pattern")
async def pin_pattern(request:Request, body: LablingModel):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # No patterns to pin in the new implementation
    return {"status_code": 200, "message": "Patterns are not used in this version"}

@app.get("/NN_cluster")
async def NN_cluster(request: Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results =  user_to_apiHelper[user].get_NN_cluster()
    return results

@app.get("/NN_classification")
async def NN_classification(request:Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results =  user_to_apiHelper[user].get_NN_classification()
    return results

@app.get("/original_dataset_order")
async def original_dataset_order(request: Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    results =  user_to_apiHelper[user].get_original_dataset_order()
    return results

@app.get("/pattern_clusters")
async def pattern_clusters(request: Request):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    # Since we're not using patterns anymore, return a simplified structure
    return {
        "data": [[]], # Empty cluster
        "group_names": ["All Examples"]  # Just one group containing everything
    }

@app.get("/test_multilabel/{iteration}/{no_annotation}")
async def test_multilabel(iteration:int, no_annotation:int):
    results = await loop.run_in_executor(executor, user_to_apiHelper['simret'].run_multi_label_test, iteration, no_annotation)
    return results

@app.post("/gpt_config")
async def set_gpt_config(request: Request, body: GPTConfigItem):
    user = request.headers.get('annotuser')
    if(user=="null" or user==None):
        return{
            "status_code":404,
            "message": "Unauthorized"
        }
    
    # Update GPT configuration for this user
    if user in user_to_apiHelper:
        # Update model in the GPT service
        user_to_apiHelper[user].gpt_service.model = body.model
        
        # Set whether to use original method or GPT for pattern synthesis
        synth = user_to_apiHelper[user].synthesizer_collector.get(user_to_apiHelper[user].selected_theme)
        if synth:
            synth.use_original_method = not body.use_gpt
            
    return {"status": "success", "config": {"model": body.model, "use_gpt": body.use_gpt}}

@app.get("/api/{user}/BERT", response_class=Response)
async def bert_annotation(user: str = "",
                 condition: str = "",
                 authorization: str = Header(None)):

    try:
        # Check if the user is authorized - use user_to_apiHelper instead of user_to_api
        if not user_to_apiHelper.get(user):
            print(f"Unauthorized access attempt for user: {user}")
            return {"status": 401, "error": "Unauthorized"}

        print(f"\n===== BERT Annotation Endpoint Called by user: {user} =====")

        # Get annotations using GPT instead of the pattern recognition system
        api_response = user_to_apiHelper[user].get_gpt_annotation()
        
        # Add some debug logging
        if isinstance(api_response, dict):
            print(f"API Response keys: {api_response.keys()}")
            if 'scores' in api_response:
                print(f"Scores count: {len(api_response['scores'])}")
                scores_sample = list(api_response['scores'].items())[:3]
                print(f"Scores sample: {scores_sample}")
            if 'explanation' in api_response:
                print(f"Explanation keys: {api_response['explanation'].keys()}")
                if 'GPT' in api_response['explanation']:
                    print(f"GPT explanations count: {len(api_response['explanation']['GPT'])}")
                    if len(api_response['explanation']['GPT']) > 0:
                        exp_sample = list(api_response['explanation']['GPT'].items())[:1]
                        print(f"Explanation sample: {exp_sample}")
        else:
            print(f"API Response is not a dict: {type(api_response)}")
        
        print(f"===== End BERT Annotation Endpoint =====\n")
        
        return JSONResponse(content=api_response)
    except Exception as e:
        import traceback
        print(f"ERROR in BERT annotation endpoint: {e}")
        traceback.print_exc()
        return JSONResponse(content={"status_code": 500, "message": f"Server error: {str(e)}"})

