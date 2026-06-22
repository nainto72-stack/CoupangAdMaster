import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('web_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'js_logic\s*=\s*\'\'\'.*?st\.markdown\(f\'<img src=\"x\" onerror=\"\{escaped_js\}\" style=\"display:none;\">\'\, unsafe_allow_html=True\)', text, re.DOTALL)
if match:
    old_js_block = match.group()
    
    new_js_block = '''            js_code = """
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
            """
            import streamlit.components.v1 as components
            components.html(js_code, height=0, width=0)'''
            
    text = text.replace(old_js_block, new_js_block)
    with open('web_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('JS replace SUCCESS')
else:
    print('Regex failed to match JS block.')
