from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
from concurrent.futures import ThreadPoolExecutor
import os


app = FastAPI()

# 🔑 Put your OpenRouter API key here
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("API key not found")

# AI models
models = {
    "ChatGPT": "openai/gpt-4o-mini",
    "Claude": "anthropic/claude-3-haiku",
    "Llama": "meta-llama/llama-3.1-8b-instruct"
}


def ask_model(model, question):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AI Jury"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": question}]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if "choices" not in result:
        return "Error: " + str(result)

    return result["choices"][0]["message"]["content"]


@app.get("/ask")
def ask(question: str):

    answers = {}

    # Run AI models in parallel
    with ThreadPoolExecutor() as executor:

        futures = {
            name: executor.submit(ask_model, model, question)
            for name, model in models.items()
        }

        for name, future in futures.items():
            answers[name] = future.result()

    judge_prompt = f"""
Question: {question}

ChatGPT:
{answers['ChatGPT']}

Claude:
{answers['Claude']}

Llama:
{answers['Llama']}

Which answer is best?

Reply ONLY with:
ChatGPT
Claude
Llama
"""

    best = ask_model("openai/gpt-4o-mini", judge_prompt).strip()

    return {
        "answers": answers,
        "best_answer": best
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<html>

<head>
<title>AI Jury</title>

<style>

body{
font-family: Arial;
margin: 0;
background: #0f172a;
color: white;
}

.container{
max-width: 1100px;
margin: auto;
padding: 40px;
}

h1{
text-align: center;
margin-bottom: 30px;
}

textarea{
width: 100%;
height: 80px;
padding: 12px;
border-radius: 8px;
border: none;
font-size: 16px;
}

button{
margin-top: 10px;
padding: 12px 20px;
font-size: 16px;
border: none;
border-radius: 8px;
background: #3b82f6;
color: white;
cursor: pointer;
}

button:hover{
background: #2563eb;
}

.grid{
display: grid;
grid-template-columns: 1fr 1fr 1fr;
gap: 20px;
margin-top: 30px;
}

.card{
background: #1e293b;
padding: 20px;
border-radius: 10px;
border: 2px solid transparent;
min-height: 200px;
}

.winner{
border: 2px solid #22c55e;
background: #052e1c;
}

.loading{
text-align: center;
margin-top: 20px;
font-size: 18px;
}

.time{
margin-top: 10px;
font-size: 14px;
color: #94a3b8;
}

</style>

</head>

<body>

<div class="container">

<h1>🤖 AI Jury</h1>

<textarea id="question" placeholder="Ask anything..."></textarea>

<button onclick="ask()">Ask AI</button>

<div id="loading" class="loading"></div>

<div id="time" class="time"></div>

<div id="results" class="grid"></div>

</div>

<script>

async function ask(){

let q = document.getElementById("question").value

if(!q) return

// Clear old results
document.getElementById("results").innerHTML = ""
document.getElementById("results").innerHTML = "<h3>⏳ Thinking...</h3>"

let res = await fetch(`/ask?question=${encodeURIComponent(q)}`)
let data = await res.json()

let container = document.getElementById("results")
container.innerHTML = ""

// Create cards first
for(let model in data.answers){

let div = document.createElement("div")

let isWinner = model === data.best_answer

div.className = isWinner ? "card winner" : "card"

div.innerHTML = `
<h3>${model} ${isWinner ? "🏆" : ""}</h3>
<p id="${model}"></p>
`

container.appendChild(div)

// Start typing animation
typeText(model, data.answers[model])
}

}


// Fake streaming typing effect
function typeText(id, text){

let el = document.getElementById(id)

let i = 0
let speed = 8   // smaller = faster

function typing(){

if(i < text.length){
    el.innerHTML += text.charAt(i)
    i++
    setTimeout(typing, speed)
}

}

typing()
}

</script>
</body>
</html>
"""