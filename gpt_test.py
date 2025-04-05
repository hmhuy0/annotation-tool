#ChatGPT

from openai import OpenAI

with open('api_key.txt', 'r') as file:
    OPENAI_API_KEY = file.read().strip()

client = OpenAI(api_key=OPENAI_API_KEY)

def call_chatgpt(prompt, system_prompt, whichModel='o3-mini'):

    if system_prompt == None:

        msg = [{"role": "user", "content": prompt}]

    else:

        msg = [{"role": "system", "content":system_prompt}, {"role": "user", "content": prompt}]

    completion = client.chat.completions.create(

        model = whichModel,

        reasoning_effort = "low",

        messages = msg,

    )

    return completion.choices[0].message.content

example_prompt = """i have below sentences:
- we really enjoyed the bbq ribs , brisket , and pulled pork . 
- the chicken biscuit with the pepper jam is a must have . 
- my only issue was the cleanliness of the restaurant . 
- the service is extremely friendly . 
- prices are high the bud is not the best . 
- our bill was around $ 400 - it was upsetting that they decided to be stingy about a $ 8 piece of cake . 
- i purchased a gibeon meteorite and black zirconium wedding band from rings unique for approximately $ 1200 . 
- the portion sizes here are gigantic .... we ordered based on our hunger level and should have ordered one plate to share . 
- only downside : three entrees served simultaneously but fourth   beet/ goat cheese ravioli   was 2 - 3 minutes later which allowed my accompaniments   delicious creamy polenta   to cool off to much . 
- omg . love this place . amazing food great staff and probably the only fancy vegan spot in town . took my carnivorous friend who also loved it . 

these sentence are about four type of content: price,service,products,environment.

please classify each sentence into possible content types. the output should provide:
{
price=True/False;indexes=[];
...
}

where the indexes is the index of that sentence that split by space, start from 0.

output example:
[
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[4,5,7,10,11]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[1,2,5,6]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=False; indexes=[]; environment=True; indexes=[6,9]},
...
]
reply as shortest as possible and remove unneccesary tokens.
"""

print(example_prompt)
response = call_chatgpt(example_prompt, None, 'o3-mini')

print(response)



"""
i have below sentences:
- we really enjoyed the bbq ribs , brisket , and pulled pork . 
- the chicken biscuit with the pepper jam is a must have . 
- my only issue was the cleanliness of the restaurant . 
- the service is extremely friendly . 
- prices are high the bud is not the best . 
- our bill was around $ 400 - it was upsetting that they decided to be stingy about a $ 8 piece of cake . 
- i purchased a gibeon meteorite and black zirconium wedding band from rings unique for approximately $ 1200 . 
- the portion sizes here are gigantic .... we ordered based on our hunger level and should have ordered one plate to share . 
- only downside : three entrees served simultaneously but fourth   beet/ goat cheese ravioli   was 2 - 3 minutes later which allowed my accompaniments   delicious creamy polenta   to cool off to much . 
- omg . love this place . amazing food great staff and probably the only fancy vegan spot in town . took my carnivorous friend who also loved it . 

these sentence are about four type of content: price,service,products,environment.

please classify each sentence into possible content types. the output should provide:
{
price=True/False;indexes=[];
...
}

where the indexes is the index of that sentence that split by space, start from 0.

output example:
[
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[4,5,7,10,11]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[1,2,5,6]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=False; indexes=[]; environment=True; indexes=[6,9]},
...
]
reply as shortest as possible and remove unneccesary tokens.

[
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[0,1,2,3,4,5,6,7,8,9,10,11,12]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[0,1,2,3,4,5,6,7,8,9,10]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=False; indexes=[]; environment=True; indexes=[0,1,2,3,4,5,6,7,8,9]},
{price=False; indexes=[]; service=True; indexes=[0,1,2,3,4,5]; products=False; indexes=[]; environment=False; indexes=[]},
{price=True; indexes=[0]; service=False; indexes=[]; products=True; indexes=[4]; environment=False; indexes=[]},
{price=True; indexes=[3,8]; service=False; indexes=[]; products=True; indexes=[15]; environment=False; indexes=[]},
{price=True; indexes=[15]; service=False; indexes=[]; products=True; indexes=[3,4,5,6,7,8,9,10,11]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]; environment=False; indexes=[]},
{price=False; indexes=[]; service=False; indexes=[]; products=True; indexes=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]; environment=False; indexes=[]},
{price=False; indexes=[]; service=True; indexes=[7]; products=True; indexes=[4]; environment=True; indexes=[3]}
]
"""