#!/usr/bin/env python3
"""Generate the frontend HTML file."""
import html

def build():
    # All the HTML/CSS/JS as a single f-string
    page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Life Sandbox — Decision Intelligence Agent</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.0/index.min.css"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5.0.0/index.min.css"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#060609;--bg2:#0b0b12;--glass:rgba(255,255,255,.035);--glass2:rgba(255,255,255,.07);--line:rgba(255,255,255,.08);--line2:rgba(255,255,255,.16);--tx:#f2f2f7;--tx2:rgba(242,242,247,.66);--tx3:rgba(242,242,247,.38);--vio:#7c6bff;--vio2:#5a48e0;--teal:#00d4aa;--pink:#ff4d8b;--amber:#ffb347;--green:#2dd4a8;--red:#ff5470;--mono:'JetBrains Mono',ui-monospace,monospace}
html,body{height:100%}
body{background:var(--bg);color:var(--tx);font-family:'Inter',system-ui,sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}
button,input,textarea{font:inherit;color:inherit}
button{cursor:pointer;background:none;border:none}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:8px}::-webkit-scrollbar-track{background:transparent}
#bg{position:fixed;inset:0;z-index:0;opacity:.55}
.grain{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.04;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}
.app{position:relative;z-index:2;display:flex;height:100vh}
.side{width:280px;flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid var(--line);background:rgba(8,8,13,.72);backdrop-filter:blur(24px);transition:margin .35s cubic-bezier(.4,0,.2,1)}
.side.hide{margin-left:-280px}
.side-top{padding:18px 16px 12px;display:flex;align-items:center;gap:10px}
.orb{width:26px;height:26px;border-radius:50%;background:conic-gradient(from 0deg,var(--vio),var(--teal),var(--pink),var(--vio));animation:spin 7s linear infinite;position:relative;flex-shrink:0}
.orb::after{content:'';position:absolute;inset:4px;border-radius:50%;background:#0a0a10}
@keyframes spin{to{transform:rotate(360deg)}}
.brand{font-size:12px;font-weight:800;letter-spacing:.22em}
.brand small{display:block;font-size:9px;letter-spacing:.18em;color:var(--tx3);font-weight:600;margin-top:2px}
.new-btn{margin:6px 16px 12px;padding:11px;border-radius:12px;background:linear-gradient(135deg,var(--vio),var(--vio2));color:#fff;font-weight:600;font-size:13px;display:flex;align-items:center;justify-content:center;gap:8px;box-shadow:0 8px 26px rgba(124,107,255,.35);transition:transform .2s,box-shadow .2s}
.new-btn:hover{transform:translateY(-1px);box-shadow:0 12px 32px rgba(124,107,255,.5)}
.side-search{margin:0 16px 14px;position:relative}
.side-search input{width:100%;padding:9px 12px 9px 32px;border-radius:10px;border:1px solid var(--line);background:var(--glass);font-size:12px;outline:none;color:var(--tx)}
.side-search svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);opacity:.4}
.side-label{padding:6px 20px;font-size:10px;letter-spacing:.2em;color:var(--tx3);font-weight:700}
.hist{flex:0 0 auto;max-height:150px;overflow-y:auto;padding:0 10px}
.hist-item{display:flex;gap:9px;align-items:center;padding:8px 10px;border-radius:10px;font-size:12.5px;color:var(--tx2);cursor:pointer;transition:background .2s,color .2s}
.hist-item:hover{background:var(--glass);color:var(--tx)}
.hist-item.on{background:var(--glass2);color:var(--tx)}
.hist-item .hd{width:6px;height:6px;border-radius:50%;background:var(--vio);flex-shrink:0;opacity:.7}
.mem-wrap{flex:1;overflow-y:auto;border-top:1px solid var(--line);margin-top:8px;padding:12px 14px 14px}
.mem{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:8px;background:var(--glass);animation:memIn .4s ease}
@keyframes memIn{from{opacity:0;transform:translateY(8px)}}
.mem p{font-size:12px;line-height:1.5}
.mem .meta{font-size:10px;color:var(--tx3);margin-top:5px;font-family:var(--mono)}
.mem .row{display:flex;gap:6px;margin-top:8px}
.mem .row button{font-size:10.5px;font-weight:600;padding:4px 10px;border-radius:999px;border:1px solid var(--line);color:var(--tx2);transition:.2s}
.mem .row button:hover{border-color:var(--line2);color:var(--tx)}
.mem .row button.ok{background:rgba(0,212,170,.14);border-color:rgba(0,212,170,.4);color:var(--teal)}
.side-foot{padding:12px 16px;border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;font-size:10.5px;color:var(--tx3);font-family:var(--mono)}
.side-foot .dot{width:6px;height:6px;border-radius:50%;background:var(--teal);box-shadow:0 0 8px var(--teal);animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.4}}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.top{display:flex;align-items:center;gap:10px;padding:12px 18px;border-bottom:1px solid var(--line);background:rgba(6,6,9,.65);backdrop-filter:blur(20px)}
.icon-btn{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);color:var(--tx2);transition:.2s;flex-shrink:0}
.icon-btn:hover{background:var(--glass);color:var(--tx)}
.icon-btn.on{background:var(--glass2);color:var(--tx);border-color:var(--line2)}
.crumb{font-size:13px;font-weight:600;color:var(--tx2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.spacer{flex:1}
.state-pill{display:flex;align-items:center;gap:7px;padding:7px 13px;border-radius:999px;border:1px solid var(--line);font-size:11.5px;color:var(--tx2);font-family:var(--mono);white-space:nowrap}
.state-pill .dot{width:7px;height:7px;border-radius:50%;background:var(--tx3)}
.state-pill.think .dot{background:var(--amber);box-shadow:0 0 8px var(--amber);animation:pulse 1s infinite}
.state-pill.run .dot{background:var(--vio);box-shadow:0 0 8px var(--vio);animation:pulse .8s infinite}
.state-pill.ok .dot{background:var(--teal);box-shadow:0 0 8px var(--teal)}
.chat{flex:1;overflow-y:auto;padding:28px 20px 20px;scroll-behavior:smooth}
.stream{max-width:840px;margin:0 auto}
.empty{display:flex;flex-direction:column;align-items:center;text-align:center;padding:8vh 10px 30px;gap:18px}
.empty .big-orb{width:74px;height:74px;border-radius:50%;background:conic-gradient(from 0deg,var(--vio),var(--teal),var(--pink),var(--amber),var(--vio));animation:spin 9s linear infinite;position:relative;box-shadow:0 0 70px rgba(124,107,255,.45)}
.empty .big-orb::after{content:'';position:absolute;inset:10px;border-radius:50%;background:var(--bg)}
.empty h1{font-size:clamp(30px,4.6vw,52px);font-weight:800;letter-spacing:-.03em;line-height:1.05;background:linear-gradient(180deg,#fff,rgba(255,255,255,.55));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.empty p{color:var(--tx2);font-size:15px;max-width:520px;line-height:1.65}
.sugs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:6px}
.sug{padding:10px 16px;border-radius:999px;border:1px solid var(--line);background:var(--glass);font-size:12.5px;color:var(--tx2);transition:.25s}
.sug:hover{border-color:rgba(124,107,255,.5);color:var(--tx);background:rgba(124,107,255,.1);transform:translateY(-2px)}
.msg{display:flex;gap:12px;margin-bottom:22px;opacity:0;transform:translateY(14px)}
.msg.in{opacity:1;transform:none;transition:opacity .45s,transform .45s cubic-bezier(.2,.8,.2,1)}
.msg.user{justify-content:flex-end}
.ububble{max-width:76%;padding:12px 16px;border-radius:18px 18px 6px 18px;background:linear-gradient(135deg,rgba(124,107,255,.22),rgba(124,107,255,.1));border:1px solid rgba(124,107,255,.35);font-size:14.5px;line-height:1.6;white-space:pre-wrap}
.av{width:32px;height:32px;border-radius:50%;background:conic-gradient(from 0deg,var(--vio),var(--teal),var(--pink),var(--vio));position:relative;flex-shrink:0;margin-top:2px;animation:spin 8s linear infinite}
.av::after{content:'';position:absolute;inset:4px;border-radius:50%;background:#0a0a10}
.abody{flex:1;min-width:0}
.ahead{display:flex;align-items:center;gap:8px;margin-bottom:7px;flex-wrap:wrap}
.aname{font-size:12.5px;font-weight:700}
.atag{font-size:9.5px;font-family:var(--mono);letter-spacing:.1em;padding:3px 8px;border-radius:999px;background:rgba(0,212,170,.12);color:var(--teal);border:1px solid rgba(0,212,170,.3)}
.atime{font-size:10px;color:var(--tx3);font-family:var(--mono)}
.atext{font-size:14.5px;line-height:1.7;color:var(--tx2);white-space:pre-wrap}
.atext b{color:var(--tx);font-weight:600}
.cursor{display:inline-block;width:2px;height:1em;background:var(--vio);vertical-align:text-bottom;margin-left:2px;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.think{display:flex;align-items:center;gap:10px;padding:4px 0}
.tdots{display:flex;gap:4px}
.tdots i{width:6px;height:6px;border-radius:50%;background:var(--vio);animation:bnc 1.2s infinite}
.tdots i:nth-child(2){animation-delay:.15s}.tdots i:nth-child(3){animation-delay:.3s}
@keyframes bnc{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-5px);opacity:1}}
.tstat{font-size:12px;color:var(--tx3);font-family:var(--mono)}
.card{border:1px solid var(--line);border-radius:18px;background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.015));margin-top:12px;overflow:hidden;backdrop-filter:blur(12px)}
.card-h{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
.card-h .k{font-size:10px;letter-spacing:.2em;font-weight:800;color:var(--vio)}
.card-h .t{font-size:13.5px;font-weight:600}
.card-h .r{margin-left:auto;font-size:10.5px;font-family:var(--mono);color:var(--tx3)}
.card-b{padding:16px 18px}
.qgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){.qgrid{grid-template-columns:1fr}}
.qf label{display:block;font-size:11px;color:var(--tx2);font-weight:600;margin-bottom:6px}
.qf .inp{display:flex;align-items:center;border:1px solid var(--line);border-radius:10px;background:rgba(0,0,0,.3);transition:border-color .2s}
.qf .inp:focus-within{border-color:var(--vio)}
.qf .pre{padding:0 0 0 11px;font-size:12px;color:var(--tx3);font-family:var(--mono)}
.qf input{flex:1;background:none;border:none;outline:none;padding:9px 11px;font-size:13px;font-family:var(--mono);min-width:0}
.chips{display:flex;gap:6px;margin-top:7px;flex-wrap:wrap}
.chip{font-size:10.5px;padding:4px 10px;border-radius:999px;border:1px solid var(--line);color:var(--tx2);font-family:var(--mono);transition:.2s}
.chip:hover{border-color:var(--teal);color:var(--teal)}
.chip.on{background:rgba(0,212,170,.14);border-color:var(--teal);color:var(--teal)}
.qfoot{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;align-items:center}
.btn{padding:10px 18px;border-radius:999px;font-size:13px;font-weight:600;transition:.25s;display:inline-flex;align-items:center;gap:8px}
.btn.pri{background:linear-gradient(135deg,var(--vio),var(--vio2));color:#fff;box-shadow:0 8px 24px rgba(124,107,255,.35)}
.btn.pri:hover{transform:translateY(-1px);box-shadow:0 12px 30px rgba(124,107,255,.5)}
.btn.gho{border:1px solid var(--line);color:var(--tx2)}
.btn.gho:hover{border-color:var(--line2);color:var(--tx)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important}
.qnote{font-size:11px;color:var(--tx3);font-family:var(--mono)}
.pipe{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:6px 0 2px}
@media(max-width:640px){.pipe{grid-template-columns:1fr 1fr}}
.pstep{border:1px solid var(--line);border-radius:14px;padding:13px;position:relative;overflow:hidden;background:rgba(0,0,0,.25);transition:border-color .3s,background .3s}
.pstep .n{font-size:9.5px;font-family:var(--mono);color:var(--tx3);letter-spacing:.15em}
.pstep .ic{position:absolute;top:11px;right:11px;width:20px;height:20px;border-radius:50%;border:1.5px solid var(--line2);display:flex;align-items:center;justify-content:center;font-size:10px;color:transparent}
.pstep .nm{font-size:13px;font-weight:700;margin:6px 0 4px}
.pstep .ds{font-size:10.5px;color:var(--tx3);line-height:1.5}
.pstep .bar{position:absolute;left:0;bottom:0;height:2px;width:0;background:linear-gradient(90deg,var(--vio),var(--teal))}
.pstep.act{border-color:rgba(124,107,255,.6);background:rgba(124,107,255,.08)}
.pstep.act .ic{border-color:var(--vio);border-top-color:transparent;animation:spin .8s linear infinite}
.pstep.act .bar{width:65%;animation:pulse 1.4s infinite}
.pstep.don{border-color:rgba(0,212,170,.45)}
.pstep.don .ic{border-color:var(--teal);color:var(--teal);background:rgba(0,212,170,.12)}
.pstep.don .bar{width:100%}
.branches{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(max-width:700px){.branches{grid-template-columns:1fr}}
.br{border:1px solid var(--line);border-radius:16px;padding:16px;background:rgba(0,0,0,.28);cursor:pointer;transition:.3s;position:relative}
.br:hover{transform:translateY(-3px);border-color:var(--line2)}
.br.sel{border-color:transparent;background:rgba(124,107,255,.08)}
.br.sel::before{content:'';position:absolute;inset:-1px;border-radius:16px;padding:1.5px;background:linear-gradient(135deg,var(--vio),var(--teal));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none}
.br .nm{font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px}
.br .nm .em{font-size:18px}
.mrow{display:flex;justify-content:space-between;gap:8px;padding:7px 0;border-bottom:1px solid var(--line);font-size:12px}
.mrow:last-child{border:none}
.mrow .l{color:var(--tx3)}
.mrow .v{font-family:var(--mono);font-weight:600}
.v.pos{color:var(--teal)}.v.neg{color:var(--pink)}.v.warn{color:var(--amber)}
.cmp{width:100%;border-collapse:collapse;font-size:12.5px}
.cmp th,.cmp td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line)}
.cmp th{font-size:10px;letter-spacing:.15em;color:var(--tx3);font-weight:700}
.cmp td:first-child{color:var(--tx2)}
.cmp td{font-family:var(--mono)}
.cmp tr:last-child td{border:none}
.cbar{height:5px;border-radius:4px;background:rgba(255,255,255,.07);margin-top:5px;overflow:hidden}
.cbar i{display:block;height:100%;border-radius:4px;width:0}
.tl{position:relative;padding-left:26px}
.tl::before{content:'';position:absolute;left:7px;top:4px;bottom:4px;width:2px;background:linear-gradient(180deg,var(--vio),var(--teal),transparent)}
.tli{position:relative;padding-bottom:18px;opacity:0;transform:translateX(-14px)}
.tli.in{opacity:1;transform:none;transition:.5s cubic-bezier(.2,.8,.2,1)}
.tli::before{content:'';position:absolute;left:-24px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--vio);box-shadow:0 0 10px var(--vio)}
.tli .m{font-size:10px;letter-spacing:.18em;color:var(--vio);font-weight:800;font-family:var(--mono)}
.tli .e{font-size:13.5px;font-weight:600;margin:3px 0}
.tli .d{font-size:12px;color:var(--tx3);line-height:1.55}
.specs{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.specs{grid-template-columns:1fr}}
.spec{border:1px solid var(--line);border-radius:14px;padding:14px;background:rgba(0,0,0,.25);transition:.25s}
.spec:hover{border-color:var(--line2);transform:translateY(-2px)}
.spec .h{display:flex;gap:10px;align-items:center;margin-bottom:9px}
.spec .a{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;background:var(--glass2)}
.spec .n{font-size:13px;font-weight:700}
.spec .r{font-size:9.5px;letter-spacing:.14em;color:var(--tx3);font-weight:700}
.spec .i{font-size:12px;color:var(--tx2);line-height:1.6}
.spec .tags{margin-top:9px;display:flex;gap:6px;flex-wrap:wrap}
.spec .tags span{font-size:9.5px;font-family:var(--mono);padding:3px 9px;border-radius:999px;background:var(--glass2);color:var(--tx2)}
.wi{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.wi input{flex:1;min-width:160px;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:rgba(0,0,0,.3);outline:none;font-family:var(--mono);font-size:13px}
.wi input:focus{border-color:var(--pink)}
.flash{animation:fl .8s ease}
@keyframes fl{0%{background:rgba(255,77,139,.25)}100%{background:transparent}}
.comp-wrap{padding:12px 20px 16px;border-top:1px solid var(--line);background:rgba(6,6,9,.7);backdrop-filter:blur(20px)}
.comp{max-width:840px;margin:0 auto;border:1px solid var(--line2);border-radius:20px;background:rgba(16,16,24,.85);box-shadow:0 16px 50px rgba(0,0,0,.45);transition:border-color .25s,box-shadow .25s}
.comp:focus-within{border-color:rgba(124,107,255,.55);box-shadow:0 16px 50px rgba(0,0,0,.45),0 0 0 3px rgba(124,107,255,.12)}
.comp textarea{width:100%;background:none;border:none;outline:none;resize:none;padding:15px 18px 6px;font-size:14.5px;line-height:1.6;max-height:180px;color:var(--tx)}
.comp textarea::placeholder{color:var(--tx3)}
.comp-bar{display:flex;align-items:center;gap:6px;padding:8px 10px 10px 14px}
.ctool{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;color:var(--tx3);transition:.2s;font-size:14px}
.ctool:hover{background:var(--glass2);color:var(--tx)}
.send{margin-left:auto;width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,var(--vio),var(--vio2));color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 20px rgba(124,107,255,.4);transition:.25s}
.send:hover{transform:translateY(-1px) scale(1.04)}
.send:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}
.hint{max-width:840px;margin:8px auto 0;font-size:10px;color:var(--tx3);font-family:var(--mono);display:flex;gap:14px;flex-wrap:wrap;justify-content:center}
.trace{width:300px;flex-shrink:0;border-left:1px solid var(--line);background:rgba(8,8,13,.72);backdrop-filter:blur(24px);display:flex;flex-direction:column;transition:margin .35s cubic-bezier(.4,0,.2,1)}
.trace.hide{margin-right:-300px}
.trace-h{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px}
.trace-h .t{font-size:10.5px;letter-spacing:.2em;font-weight:800;color:var(--tx2)}
.trace-h .live{width:6px;height:6px;border-radius:50%;background:var(--red);animation:pulse 1.2s infinite}
.trace-log{flex:1;overflow-y:auto;padding:12px 14px;font-family:var(--mono);font-size:10.5px;line-height:1.5}
.tle{display:flex;gap:8px;padding:5px 0;border-bottom:1px dashed rgba(255,255,255,.05);opacity:0;transform:translateY(6px)}
.tle.in{opacity:1;transform:none;transition:.35s}
.tle .tm{color:var(--tx3);flex-shrink:0}
.tle .tg{flex-shrink:0;font-weight:700;padding:0 5px;border-radius:4px;height:fit-content}
.tg.PARSE{background:rgba(124,107,255,.18);color:#b7abff}
.tg.MEM{background:rgba(255,179,71,.16);color:var(--amber)}
.tg.SIM{background:rgba(0,212,170,.15);color:var(--teal)}
.tg.AGENT{background:rgba(255,77,139,.15);color:var(--pink)}
.tg.SYS{background:rgba(255,255,255,.08);color:var(--tx3)}
.tle .ms{color:var(--tx2);word-break:break-word}
@media(max-width:1100px){.trace{position:fixed;right:0;top:0;bottom:0;z-index:40;margin-right:0;transform:translateX(100%);transition:transform .35s}.trace.show-m{transform:none}}
@media(max-width:860px){.side{position:fixed;left:0;top:0;bottom:0;z-index:40;margin-left:0;transform:translateX(-100%);transition:transform .35s}.side.show-m{transform:none}.qgrid{grid-template-columns:1fr}}
</style>
</head>
<body>
<canvas id="bg"></canvas>
<div class="grain"></div>
<div class="app">
  <aside class="side" id="side">
    <div class="side-top"><div class="orb"></div><div class="brand">LIFE SANDBOX<small>DECISION INTELLIGENCE</small></div></div>
    <button class="new-btn" id="newChat"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg> New decision</button>
    <div class="side-search"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input placeholder="Search decisions&hellip;"/></div>
    <div class="side-label">RECENT</div><div class="hist" id="hist"></div>
    <div class="side-label" style="margin-top:10px">SAVED CONTEXT &middot; MEMORY</div>
    <div class="mem-wrap" id="memWrap"></div>
    <div class="side-foot"><span class="dot"></span>deterministic core v2 &middot; online</div>
  </aside>
  <main class="main">
    <div class="top">
      <button class="icon-btn" id="sideToggle" title="Sidebar"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
      <div class="crumb" id="crumb">New decision</div>
      <div class="spacer"></div>
      <div class="state-pill" id="statePill"><span class="dot"></span><span id="stateTxt">idle</span></div>
      <button class="icon-btn on" id="traceToggle" title="Process trace"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h10M4 18h7"/></svg></button>
    </div>
    <div class="chat" id="chat"><div class="stream" id="stream">
      <div class="empty" id="empty">
        <div class="big-orb"></div><h1>Explore the futures<br/>before you decide.</h1>
        <p>I'm your personal decision agent. Tell me the choice you're facing &mdash; I'll interpret it, ask only for what I truly need, simulate every branch deterministically, and show my work.</p>
        <div class="sugs">
          <button class="sug">I have ₹50,000. Should I buy a laptop,