"""Audio Guide widget component injecting Web Speech API JS listener and floating control bar."""
import json
import streamlit as st
import streamlit.components.v1 as components
from guide_content import get_guide_sentences

LANG_SPEECH_CODES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Bengali": "bn-IN",
    "Odia": "or-IN",
    "Telugu": "te-IN",
}


def render_guide(lang: str, enabled: bool):
    """Inject floating audio guide widget and parent window event listeners."""
    guide_dict = get_guide_sentences(lang)
    lang_code = LANG_SPEECH_CODES.get(lang, "en-IN")

    guide_json_str = json.dumps(guide_dict, ensure_ascii=False)
    enabled_str = "true" if enabled else "false"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #guide-widget {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 330px;
                background: #1e272e;
                color: #f1f2f6;
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 12px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.6);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                z-index: 99999;
                display: {"block" if enabled else "none"};
            }}
            .widget-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
                font-weight: bold;
                color: #3498db;
                font-size: 0.95rem;
            }}
            .caption-box {{
                background: rgba(0,0,0,0.45);
                border-radius: 6px;
                padding: 8px;
                font-size: 0.85rem;
                min-height: 46px;
                max-height: 75px;
                overflow-y: auto;
                margin-bottom: 6px;
                border-left: 3px solid #2ecc71;
                line-height: 1.3;
            }}
            .warning-note {{
                font-size: 0.75rem;
                color: #f39c12;
                margin-bottom: 6px;
            }}
            .ctrl-btn {{
                background: #34495e;
                color: white;
                border: none;
                padding: 5px 9px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.75rem;
                margin-right: 3px;
            }}
            .ctrl-btn:hover {{
                background: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div id="guide-widget">
            <div class="widget-header">
                <span>🔊 Audio Guide ({lang})</span>
                <span id="guide-status">{"ACTIVE" if enabled else "OFF"}</span>
            </div>
            <div class="caption-box" id="caption-text">
                Click or hover over any section to listen to explanation...
            </div>
            <div id="warning-text" class="warning-note" style="display:none;"></div>
            <div style="display: flex; justify-content: space-between;">
                <button class="ctrl-btn" onclick="toggleMute()" id="btn-mute">Mute</button>
                <button class="ctrl-btn" onclick="replayLast()">Replay</button>
                <button class="ctrl-btn" onclick="stopSpeech()">Stop</button>
                <button class="ctrl-btn" onclick="toggleHover()" id="btn-hover">Hover: ON</button>
            </div>
        </div>

        <script>
            const GUIDE = {guide_json_str};
            const TARGET_LANG = "{lang_code}";
            const IS_ENABLED = {enabled_str};

            let isMuted = false;
            let hoverEnabled = true;
            let lastKey = "";
            let lastSpokenTime = {{}};
            let hoverTimer = null;
            let currentUtterance = null;
            let hasWelcomed = false;

            function updateCaption(text) {{
                document.getElementById('caption-text').innerText = text;
            }}

            function checkVoiceSupport() {{
                if (!('speechSynthesis' in window)) return null;
                const voices = window.speechSynthesis.getVoices();
                if (!voices || voices.length === 0) return null;

                let voice = voices.find(v => v.lang === TARGET_LANG || v.lang.replace('_', '-').startsWith(TARGET_LANG));
                if (!voice) {{
                    voice = voices.find(v => v.lang.startsWith('hi') || v.lang.startsWith('en'));
                    document.getElementById('warning-text').innerText = "⚠️ Voice for {lang} not available on device. Showing text caption.";
                    document.getElementById('warning-text').style.display = "block";
                }}
                return voice;
            }}

            function speakKey(key, force = false) {{
                if (!IS_ENABLED || isMuted) return;
                const text = GUIDE[key];
                if (!text) return;

                const now = Date.now();
                if (!force && lastSpokenTime[key] && (now - lastSpokenTime[key] < 8000)) {{
                    return;
                }}

                lastSpokenTime[key] = now;
                lastKey = key;
                updateCaption(text);

                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const utt = new SpeechSynthesisUtterance(text);
                    const voice = checkVoiceSupport();
                    if (voice) utt.voice = voice;
                    utt.lang = TARGET_LANG;
                    utt.rate = 0.95;
                    currentUtterance = utt;
                    window.speechSynthesis.speak(utt);
                }}
            }}

            function stopSpeech() {{
                if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            }}

            function replayLast() {{
                if (lastKey) speakKey(lastKey, true);
            }}

            function toggleMute() {{
                isMuted = !isMuted;
                document.getElementById('btn-mute').innerText = isMuted ? "Unmute" : "Mute";
                if (isMuted) stopSpeech();
            }}

            function toggleHover() {{
                hoverEnabled = !hoverEnabled;
                document.getElementById('btn-hover').innerText = hoverEnabled ? "Hover: ON" : "Hover: OFF";
            }}

            try {{
                const parentDoc = window.parent.document;

                if (IS_ENABLED) {{
                    parentDoc.addEventListener('click', function(e) {{
                        if (!hasWelcomed) {{
                            hasWelcomed = true;
                            speakKey('welcome', true);
                        }}

                        const target = e.target;
                        if (target.closest('[role="tab"]')) {{
                            const tabText = target.closest('[role="tab"]').innerText.toLowerCase();
                            if (tabText.includes('home')) speakKey('tab_home', true);
                            else if (tabText.includes('overview')) speakKey('tab_overview', true);
                            else if (tabText.includes('risk map')) speakKey('tab_map', true);
                            else if (tabText.includes('infra')) speakKey('tab_infra', true);
                            else if (tabText.includes('advisory')) speakKey('tab_advisory', true);
                            else if (tabText.includes('insurance')) speakKey('tab_insurance', true);
                        }} else if (target.closest('[data-testid="stMetric"]')) {{
                            speakKey('kpi_strip', true);
                        }} else if (target.closest('button') && target.closest('button').innerText.includes('Generate')) {{
                            speakKey('advisory_generate', true);
                        }}
                    }}, {{ passive: true }});

                    parentDoc.addEventListener('mouseover', function(e) {{
                        if (!hoverEnabled) return;
                        clearTimeout(hoverTimer);
                        const target = e.target;

                        hoverTimer = setTimeout(() => {{
                            if (target.closest('[data-testid="stSidebar"]')) {{
                                speakKey('sidebar_region');
                            }} else if (target.closest('iframe')) {{
                                speakKey('map_area');
                            }} else if (target.closest('[data-testid="stMetric"]')) {{
                                speakKey('kpi_strip');
                            }}
                        }}, 700);
                    }}, {{ passive: true }});
                }}
            }} catch(err) {{
                console.log("Audio Guide delegation notice:", err);
            }}

            if ('speechSynthesis' in window) {{
                window.speechSynthesis.onvoiceschanged = checkVoiceSupport;
            }}
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=140)


def speak_custom_sentence(text: str, lang: str, nonce: str):
    """Render a tiny components.html block to speak a dynamic Python sentence via Web Speech API."""
    lang_codes = {"English": "en-IN", "Hindi": "hi-IN", "Bengali": "bn-IN", "Odia": "or-IN", "Telugu": "te-IN"}
    lang_code = lang_codes.get(lang, "en-IN")
    escaped_text = json.dumps(text, ensure_ascii=False)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <body>
    <script>
    (function() {{
        try {{
            const win = window.parent;
            if ('speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const utt = new win.SpeechSynthesisUtterance({escaped_text});
                utt.lang = "{lang_code}";
                utt.rate = 0.95;
                const voices = win.speechSynthesis.getVoices();
                let voice = voices.find(v => v.lang === "{lang_code}" || v.lang.replace('_', '-').startsWith("{lang_code}"));
                if (!voice) {{
                    voice = voices.find(v => v.lang.startsWith('hi') || v.lang.startsWith('en'));
                }}
                if (voice) utt.voice = voice;
                win.speechSynthesis.speak(utt);
            }}
        }} catch(e) {{
            console.log("Speech utterance notice:", e);
        }}
    }})();
    </script>
    <!-- Nonce: {nonce} -->
    </body>
    </html>
    """
    components.html(html_code, height=0, width=0)
