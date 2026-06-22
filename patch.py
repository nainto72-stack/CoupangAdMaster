import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('web_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_trigger = """# ── 우클릭 메뉴 통신용 숨겨진 입력 위젯 및 파이썬 핸들러 ──
st.markdown("<div id='hidden-kw-trigger-wrapper' style='position:absolute; top:-9999px; left:-9999px; opacity:0; pointer-events:none;'>", unsafe_allow_html=True)
trigger_val = st.text_input("kw_trigger", key="kw_trigger_input", label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)"""

new_trigger = """# ── 우클릭 메뉴 통신용 완벽 숨김 입력창 핸들러 ──
st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='kw_mover_secret_trigger']) { display: none !important; }</style>", unsafe_allow_html=True)
trigger_val = st.text_input("kw_mover_secret_trigger", key="kw_mover_trigger", label_visibility="collapsed")"""

if old_trigger in text:
    text = text.replace(old_trigger, new_trigger)
    print("Trigger replaced")

old_js_start = """            js_code = \"\"\"
            <script>
            (function(){
                var parentDoc = window.parent.document;"""

old_js_end = """            escaped_js = js_logic.replace(\"\\n\", \" \").replace('\"', \"&quot;\")
            st.markdown(f'<img src=\"x\" onerror=\"{escaped_js}\" style=\"display:none;\">', unsafe_allow_html=True)"""

idx1 = text.find(old_js_start)
idx2 = text.find(old_js_end)
if idx1 != -1 and idx2 != -1:
    idx2 += len(old_js_end)
    old_js_block = text[idx1:idx2]
    
    new_js_block = """            js_code = \"\"\"
            <script>
            (function(){
                var parentDoc = window.parent.document;

                window.parent.doAction = function(action){
                    var menu = parentDoc.getElementById("ctx-menu");
                    if(!menu) return;
                    var kw = menu.dataset.kw || "";
                    if(kw && action){
                        try {
                            var inputs = parentDoc.querySelectorAll('input[aria-label="kw_mover_secret_trigger"]');
                            if(inputs.length > 0) {
                                var input = inputs[inputs.length - 1];
                                var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                                nativeSetter.call(input, action + "|||" + kw + "|||" + Date.now());
                                input.dispatchEvent(new Event("input", { bubbles: true }));
                                input.dispatchEvent(new Event("change", { bubbles: true }));
                                input.focus({preventScroll: true});
                                setTimeout(function(){ input.blur(); }, 100);
                            }
                        }catch(e){console.error(e);}
                    }
                    menu.style.display="none";
                };

                var sortState={};
                function sortTable(ci){
                    var tb = parentDoc.querySelector("#orange-keyword-table tbody");
                    if(!tb)return;
                    var rows = Array.from(tb.querySelectorAll("tr.keyword-row"));
                    var desc = !sortState[ci];
                    sortState[ci] = desc;
                    rows.sort(function(a,b){
                        var at=(a.cells[ci]?a.cells[ci].innerText:"").trim();
                        var bt=(b.cells[ci]?b.cells[ci].innerText:"").trim();
                        var an=parseFloat(at.replace(/[^0-9.\\-]/g,""));
                        var bn=parseFloat(bt.replace(/[^0-9.\\-]/g,""));
                        if(!isNaN(an)&&!isNaN(bn))return desc?bn-an:an-bn;
                        return desc?bt.localeCompare(at,"ko"):at.localeCompare(bt,"ko");
                    });
                    rows.forEach(function(r){tb.appendChild(r);});
                    parentDoc.querySelectorAll("#orange-keyword-table th").forEach(function(th,i){
                        var sp=th.querySelector(".sort-arrow");
                        if(sp)sp.innerText="";
                        if(i===ci){
                            if(!sp){
                                sp=parentDoc.createElement("span");
                                sp.className="sort-arrow";
                                sp.style.marginLeft="4px";
                                th.appendChild(sp);
                            }
                            sp.innerText=desc?" ▼":" ▲";
                        }
                    });
                }

                function bindHeaders(){
                    parentDoc.querySelectorAll("#orange-keyword-table th").forEach(function(th,i){
                        if(th.dataset.sortBound)return;
                        th.dataset.sortBound="1";
                        th.style.cursor="pointer";
                        th.addEventListener("click",function(){sortTable(i);});
                    });
                }

                var selRow = null;
                function showMenu(e, kw, row){
                    e.preventDefault();
                    e.stopPropagation();
                    if(selRow && selRow !== row) selRow.style.backgroundColor="#E65100";
                    selRow = row;
                    row.style.backgroundColor="#1d4ed8";
                    var menu = parentDoc.getElementById("ctx-menu");
                    if(!menu) return;
                    var title = parentDoc.getElementById("ctx-kw-title");
                    if(title) title.innerText="🔑 "+kw;
                    menu.dataset.kw = kw;
                    menu.style.display="block";
                    var x = e.clientX, y = e.clientY;
                    if(x+215 > window.parent.innerWidth) x = window.parent.innerWidth-220;
                    if(y+240 > window.parent.innerHeight) y = window.parent.innerHeight-245;
                    menu.style.left = x+"px";
                    menu.style.top = y+"px";
                    setTimeout(function(){
                        parentDoc.addEventListener("click", hideMenu, {once:true});
                    }, 50);
                }

                function hideMenu(){
                    var m = parentDoc.getElementById("ctx-menu");
                    if(m) m.style.display="none";
                }
                
                function bindRows(){
                    parentDoc.querySelectorAll("tr.keyword-row").forEach(function(row){
                        if(row.dataset.bound)return;
                        row.dataset.bound="1";
                        row.addEventListener("click",function(){
                            if(selRow && selRow !== row) selRow.style.backgroundColor="#E65100";
                            selRow = row;
                            row.style.backgroundColor="#1d4ed8";
                        });
                        row.addEventListener("contextmenu",function(e){
                            showMenu(e, row.dataset.keyword||"", row);
                        });
                    });
                }
                
                var attempts = 0;
                function tryBind(){
                    var tb = parentDoc.querySelector("#orange-keyword-table tbody");
                    if(tb){
                        bindRows();
                        bindHeaders();
                    } else if(attempts < 10){
                        attempts++;
                        setTimeout(tryBind, 200);
                    }
                }
                setTimeout(tryBind, 500);
            })();
            </script>
            \"\"\"
            import streamlit.components.v1 as components
            components.html(js_code, height=0, width=0)"""

    text = text.replace(old_js_block, new_js_block)
    print("JS block replaced")

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
