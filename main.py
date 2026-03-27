from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
from concurrent.futures import ThreadPoolExecutor
import os
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("API key not found")

models = {
    "ChatGPT": "openai/gpt-4o-mini",
    "Claude": "anthropic/claude-3-haiku",
    "Llama": "meta-llama/llama-3.1-8b-instruct"
}

# ✅ chat memory
chat_history = []

def ask_model(model, question):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # ✅ FIX: safe copy of memory
    messages = list(chat_history) + [{"role": "user", "content": question}]

    data = {
        "model": model,
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except:
        return f"Error: {response.text}"

##############################################################################################
@app.get("/ask")
def ask(question: str):

    def generate():

        # ✅ 1. ADD USER QUESTION FIRST
        chat_history.append({"role": "user", "content": question})

        answers = {}

        with ThreadPoolExecutor() as executor:
            futures = {
                name: executor.submit(ask_model, model, question)
                for name, model in models.items()
            }

            for name, future in futures.items():
                result = future.result()
                answers[name] = result

                yield f"data: {json.dumps({'model': name, 'answer': result})}\n\n"

        # judge
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

        best = ask_model("anthropic/claude-3-haiku", judge_prompt).strip()

        if best not in answers:
            best = "ChatGPT"

        yield f"data: {json.dumps({'best': best})}\n\n"

        # ✅ 2. STORE ALL ANSWERS
        chat_history.append({
            "role": "assistant",
            "content": f"""
ChatGPT: {answers['ChatGPT']}
Claude: {answers['Claude']}
Llama: {answers['Llama']}
"""
        })

        # ✅ 3. TRIM MEMORY
        chat_history[:] = chat_history[-10:]

    return StreamingResponse(generate(), media_type="text/event-stream")

###########################################
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<html>
<head>
<title>AI Jury Chat</title>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<style>
body{
font-family: Arial;
background:#0f172a;
color:white;
padding:20px;
}

.box{
margin-bottom:30px;
}

textarea{
width:100%;
height:70px;
padding:10px;
border-radius:8px;
border:none;
}

button{
margin-top:10px;
padding:10px 15px;
border:none;
border-radius:8px;
background:#3b82f6;
color:white;
cursor:pointer;
}

.grid{
display:grid;
gap:10px;
margin-top:15px;
}

.grid.all {
    grid-template-columns: 1fr 1fr 1fr;
}

.grid.best {
    grid-template-columns: 1fr;
}

.card{
background:#1e293b;
padding:10px;
border-radius:8px;
}

.winner{
border:2px solid #22c55e;
}

.card h3 {
    margin: 5px 0;
    font-size: 18px;
}

.card strong {
    color: #22c55e;
}


.card strong {
    color: #22c55e;
}

/* ✅ ADD AFTER THIS */
.card-header{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:8px;
}

.actions button{
    margin-left:5px;
    border:none;
    background:#334155;
    color:white;
    padding:4px 8px;
    border-radius:5px;
    cursor:pointer;
}

.actions button:hover{
    background:#475569;
}

.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
}

.switch input {
  display: none;
}

.slider {
  position: absolute;
  cursor: pointer;
  background-color: #334155;
  border-radius: 30px;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  transition: 0.3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
}

input:checked + .slider {
  background-color: #22c55e;
}

input:checked + .slider:before {
  transform: translateX(30px);
}

.card{
    background:#1e293b;
    padding:10px;
    border-radius:8px;

    transition: all 0.3s ease;
    opacity: 1;
    transform: scale(1);
}

.skeleton {
    background: linear-gradient(
        90deg,
        #1e293b 25%,
        #334155 50%,
        #1e293b 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.2s infinite;
    border-radius: 8px;
    height: 80px;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.card.hide {
    display: none;   /* ✅ THIS is the key fix */
}

.grid{
    display:grid;
    gap:10px;
    margin-top:15px;
    transition: all 0.3s ease;
}


.theme-bar{
    display:flex;
    align-items:center;
    width:120px;   /* 50% width */
    border-radius:6px;
    margin-bottom:20px;
}

.color-box{
    width:30px;
    height:30px;
    border-radius:6px;
    cursor:pointer;
}

.color-box.active{
    outline:3px solid white;
}

body{
    transition: background 0.3s ease;
}

.top-bar{
    display:flex;
    align-items:center;
    gap:15px;   /* controls space between toggle & colors */
}

.toggle-group{
    display:flex;
    align-items:center;
    gap:10px;
}

.theme-bar{
    display:flex;
    gap:4px;
    align-items:center;
    flex-shrink:0; 
}
</style>

</head>

<body>

<h1>🤖 AI Jury Chat</h1>

<div class="top-bar">

    <div class="toggle-group">
        <span id="labelAll" style="color:#22c55e;">All</span>

        <label class="switch">
            <input type="checkbox" id="viewToggle" onchange="toggleView(this)">
            <span class="slider"></span>
        </label>

        <span id="labelBest">Best</span>
    </div>

    <!-- ✅ MOVE COLORS HERE -->
    <div class="theme-bar">

        <div class="color-box"
             style="background:linear-gradient(90deg,#000000,#3E454B)"
             onclick="setTheme('#000000','#3E454B', this)"></div>

        <div class="color-box"
             style="background:linear-gradient(90deg,#010048,#000000)"
             onclick="setTheme('#010048','#000000', this)"></div>

        <div class="color-box"
             style="background:linear-gradient(90deg,#3E454B,#828282)"
             onclick="setTheme('#3E454B','#828282', this)"></div>

        <div class="color-box"
             style="background:#ffffff; border:1px solid #ccc"
             onclick="setTheme('#ffffff','#ffffff', this)"></div>

    </div>

</div>

<div id="chat"></div>

<script>

speechSynthesis.onvoiceschanged = () => {
    speechSynthesis.getVoices()
}

let currentView = "all"  // default

// typing effect
function typeText(el, text){
    let i = 0
    let temp = ""   // ✅ ADD THIS LINE

    function typing(){
        if(i < text.length){
            temp += text.charAt(i)
            el.innerHTML = marked.parse(temp)
            i++
            setTimeout(typing, 8)
        }
    }
    typing()
}

// create input

function createInputBox(){

    let chat = document.getElementById("chat")

    // ✅ REMOVE Ask button from previous input
    let oldBtns = document.querySelectorAll(".box button")
    oldBtns.forEach(btn => btn.remove())

    let box = document.createElement("div")
    box.className = "box"

    let id = Date.now()

    box.innerHTML = `
    <textarea id="q_${id}" placeholder="Ask something..." 
    onkeydown="handleKey(event, ${id})"></textarea>
    <br>
    <button onclick="ask(${id})">Ask</button>
    <div id="res_${id}"></div>
    `

    chat.appendChild(box)
}


// ask function
async function ask(id){

// 🔥 REMOVE Ask button from current box after click
let btn = document.querySelector(`#q_${id}`).parentNode.querySelector("button")
if(btn){
    btn.remove()
}

let q = document.getElementById("q_"+id).value
if(!q) return

// disable after submit


let oldBox = document.getElementById("q_"+id)
let text = oldBox.value

let p = document.createElement("div")
p.className = "card"
p.innerText = text

oldBox.parentNode.replaceChild(p, oldBox)

let resDiv = document.getElementById("res_"+id)
resDiv.innerHTML = "⏳ Thinking..."


let cards = {}


let eventSource = new EventSource(`/ask?question=${encodeURIComponent(q)}`)

let grid = document.createElement("div")
grid.className = "grid " + currentView

resDiv.innerHTML = ""
resDiv.appendChild(grid)

let loadingCards = []

let count = currentView === "best" ? 1 : 3

for(let i=0; i<count; i++){
    let div = document.createElement("div")
    div.className = "card"

    let skeleton = document.createElement("div")
    skeleton.className = "skeleton"

    // ✅ ADD THESE LINES (YOU MISSED THESE)
    div.appendChild(skeleton)
    grid.appendChild(div)

    loadingCards.push(div)
}


eventSource.onmessage = function(event){

    let data = JSON.parse(event.data)

    // 🟢 Answer arrives
    if(data.model){

        if(loadingCards.length > 0){
            loadingCards[0].remove()
            loadingCards.shift()
        }

        let model = data.model
        let answer = data.answer

        let div = document.createElement("div")
        div.className = "card"

        let uniqueId = model + "_" + id

        div.innerHTML = `
        <div class="card-header">
            <h4>${model}</h4>
            <div class="actions">
                <button onclick="copyText('${uniqueId}')">📋</button>
                <button id="btn_${uniqueId}" onclick="toggleSpeech('${uniqueId}')">🔊</button>
            </div>
        </div>
        <p id="${uniqueId}"></p>
        `

        // 🔥 KEY LOGIC
        if(currentView === "best"){
            div.classList.add("hide")   // hide in best mode
        }

        grid.appendChild(div)

        cards[model] = div

        // ✅ typing always starts (important)
        typeText(document.getElementById(uniqueId), answer)
    }

    // 🏆 Winner arrives later
    if(data.best){

        let winner = data.best

        if(cards[winner]){

            cards[winner].classList.add("winner")

            if(currentView === "best"){

                // hide all
                Object.values(cards).forEach(card => {
                    card.classList.add("hide")
                })

                // show only winner
                cards[winner].classList.remove("hide")
            }
        }

        eventSource.close()
    }
}

eventSource.onerror = function(e){
    console.log("❌ SSE ERROR", e)

    if(eventSource.readyState === EventSource.CLOSED){
        console.log("Connection closed")
    }

    eventSource.close()
}


// ✅ Apply current toggle state to new grid

if(currentView === "best"){
    grid.style.gridTemplateColumns = "1fr"
}

// next input box
createInputBox()
}

// enter key
function handleKey(e, id){
if(e.key === "Enter" && !e.shiftKey){
e.preventDefault()
ask(id)
}
}

function toggleView(el){

    if(el.checked){
        currentView = "best"
    } else {
        currentView = "all"
    }

    let grids = document.querySelectorAll(".grid")

    grids.forEach(grid => {

        // ✅ update layout
        grid.classList.remove("all", "best")
        grid.classList.add(currentView)

        // 🔥 FORCE GRID LAYOUT
        if(currentView === "all"){
            grid.style.gridTemplateColumns = "1fr 1fr 1fr"
        } else {
            grid.style.gridTemplateColumns = "1fr"
        }
                let cards = grid.children
        for(let card of cards){
            let isWinner = card.classList.contains("winner")

            if(currentView === "best"){
                if(isWinner){
                    card.classList.remove("hide")
                } else {
                    card.classList.add("hide")
                }
            } else {
                card.classList.remove("hide")
            }
        }
    })
}


function setTheme(color1, color2, el){

    let isLight = color1 === "#ffffff"

    // background
    document.body.style.background = isLight
        ? "#ffffff"
        : `linear-gradient(135deg, ${color1}, ${color2})`

    // text color
    document.body.style.color = isLight ? "#000" : "#fff"

    // cards
    document.querySelectorAll(".card").forEach(card => {
        card.style.background = isLight ? "#f1f5f9" : "#1e293b"
        card.style.color = isLight ? "#000" : "#fff"
    })

    // buttons
    document.querySelectorAll("button").forEach(btn => {
        btn.style.background = isLight ? "#e2e8f0" : "#3b82f6"
        btn.style.color = isLight ? "#000" : "#fff"
    })

    // active highlight
    document.querySelectorAll(".color-box").forEach(box => {
        box.classList.remove("active")
    })
    el.classList.add("active")

    // save
    localStorage.setItem("theme", JSON.stringify({color1, color2}))
}

/* optional restore */
window.onload = () => {
    let saved = localStorage.getItem("theme")

    if(saved){
        let {color1, color2} = JSON.parse(saved)
        document.body.style.background = `linear-gradient(135deg, ${color1}, ${color2})`
    }
}


// first input
createInputBox()

// 📋 Copy
function copyText(id){
    let text = document.getElementById(id).innerText
    navigator.clipboard.writeText(text)
}

let currentSpeechId = null

function toggleSpeech(id){

    let btn = document.getElementById("btn_" + id)

    if(currentSpeechId === id){
        window.speechSynthesis.cancel()
        currentSpeechId = null
        btn.innerText = "🔊"
        return
    }

    window.speechSynthesis.cancel()

    let text = document.getElementById(id).innerText

    let speech = new SpeechSynthesisUtterance(text)

    let voices = speechSynthesis.getVoices()
    let selectedVoice =
        voices.find(v => v.name.includes("Google UK English Female")) ||
        voices.find(v => v.lang === "en-US") ||
        voices[0]

    speech.voice = selectedVoice
    speech.rate = 0.85
    speech.pitch = 0.9

    currentSpeechId = id
    btn.innerText = "⏹"

    speech.onend = () => {
        btn.innerText = "🔊"
        currentSpeechId = null   // ✅ FIX THIS LINE (your line was cut)
    }

    window.speechSynthesis.speak(speech)
}

</script>

</body>
</html>
"""