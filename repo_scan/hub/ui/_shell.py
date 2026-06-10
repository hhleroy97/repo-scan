"""``</head>``, body chrome (header, nav, viewer, toast), and ``<script>`` open."""

_FRAGMENT = r"""</head>
<body>
<header><h1 id="repo">repo-scan</h1>
<span class="sub"><span id="status-pill" hidden></span><span id="meta"></span></span></header>
<div id="busy-bar" aria-hidden="true"></div>
<main id="main"><div class="empty">Loading…</div></main>
<nav>
  <a href="#now" class="active" data-tab="now">Now</a>
  <a href="#gates" data-tab="gates">Gates<span class="n" id="ngates" hidden></span></a>
  <a href="#tickets" data-tab="tickets">Tickets<span class="n" id="ntickets" hidden></span></a>
  <a href="#activity" data-tab="activity">Activity</a>
  <a href="#dashboard" data-tab="dashboard">Dashboard</a>
</nav>
<div id="viewer"><div class="bar">
  <button class="ghost" style="flex:none;padding:7px 14px" onclick="closeDoc()">Close</button>
  <span class="path" id="docpath"></span></div><pre id="doctext"></pre></div>
<div id="toast"></div>
<script>
"""
