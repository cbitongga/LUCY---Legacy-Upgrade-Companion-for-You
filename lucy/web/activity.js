'use strict';

// Local SVGs share one visual language; no image downloads or icon dependencies.
const AGENT_GLYPHS = {
  orchestrator: '<circle cx="12" cy="5" r="3"/><rect x="2" y="16" width="6" height="5" rx="1"/><rect x="16" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M5 16v-4h14v4"/>',
  intelligence: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M7 10h6M10 7v6"/>',
  architect: '<path d="M3 21 12 3l9 18H3ZM8 15h8M10 11h4M12 3v18"/>',
  implementation: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
  test: '<path d="M8 3h8M9 3v7L4 19q-1 2 2 2h12q3 0 2-2l-5-9V3M7 15h10m-7 3 2 1 3-3"/>',
  differential: '<path d="M8 4H3v16h5M16 4h5v16h-5M7 9h10l-3-3m3 9H7l3 3"/>',
  critic: '<path d="M4 4h16v12H9l-5 4V4ZM12 7v4"/><circle cx="12" cy="14" r=".6"/>',
  adversarial: '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4ZM13 6l-5 7h4l-1 5 5-7h-4l1-5Z"/>',
  remediation: '<path d="M14 3a6 6 0 0 0-7 8L2 17a3 3 0 0 0 5 4l6-6a6 6 0 0 0 8-7l-4 4-5-5 2-4Z"/>',
  guardian: '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4ZM7 12l3 3 7-7"/>',
  assurance: '<rect x="5" y="4" width="14" height="18" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="m8 13 3 3 5-6M9 19h6"/>',
  memory: '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/>',
  cloud: '<path d="M7 18a5 5 0 1 1-1-10 7 7 0 0 1 13-1 5 5 0 0 1 0 10M12 12v10m-3-3 3 3 3-3"/>',
  stability: '<circle cx="12" cy="12" r="10"/><path d="M3 12h5l2-4 4 8 2-4h5"/>',
  knowledge: '<path d="M12 6Q7 2 2 5v15q5-3 10 0 5-3 10 0V5q-5-3-10 1Zm0 0v14M5 9l4 1m6 0 4-1M5 13l4 1m6 0 4-1"/>',
  forecast: '<path d="M3 3v18h18M6 16l5-6 4 3 6-8m-5 0h5v5"/>',
  observability: '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z"/><circle cx="12" cy="12" r="3"/>',
  interviewer: '<path d="M2 3h14v11H8l-5 4v-4H2V3Zm16 5h4v13l-4-3h-6v-2M6 7h6M6 10h4"/>'
};
const ACTIVITY_LABELS = {working:'Working now',waiting:'Waiting',completed:'Completed',failed:'Needs attention',paused:'Paused',interrupted:'Worker interrupted',cancelled:'Cancelled',stale:'Outdated',idle:'Idle',not_configured:'Not configured',pending:'Up next',blocked:'Blocked'};

function agentIcon(id) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${AGENT_GLYPHS[id] || AGENT_GLYPHS.orchestrator}</svg>`;
}

function agentStateLabel(status) {
  return ACTIVITY_LABELS[status] || 'Unknown';
}


function robotIcon(id) {
  return `<span class="robot-shell"><svg class="robot-body" viewBox="0 0 80 84" aria-hidden="true"><path d="M40 6v9"/><circle cx="40" cy="5" r="3"/><rect x="13" y="17" width="54" height="42" rx="16"/><rect class="robot-visor" x="21" y="27" width="38" height="20" rx="8"/><path class="robot-eyes" d="M30 34v6m20-6v6"/><path d="M5 32v15m70-15v15M28 60v8m24-8v8"/><rect x="22" y="65" width="36" height="12" rx="6"/></svg><span class="robot-specialty">${agentIcon(id)}</span></span>`;
}
function mapNode(agent,child=false) {
  return `<button class="map-node agent-${esc(agent.status)} ${child?'child-node':''} ${state.selectedAgent===agent.id?'node-selected':''}" data-action="inspect-agent" data-agent="${esc(agent.id)}" aria-label="${esc(agent.name)}: ${esc(agentStateLabel(agent.status))}. View assignment" title="${esc(agent.task)}">
    ${robotIcon(agent.role||agent.id)}<strong>${esc(agent.name)}</strong><span class="agent-state"><i></i>${esc(agentStateLabel(agent.status))}</span>${child?'<small>SUBAGENT</small>':''}</button>`;
}
function activityPanel(compact=false) {
  const activity=state.activity;
  if(!activity) return '<div class="card empty"><h2>Your crew is ready</h2><p>Create or open a project to give LUCY a mission.</p></div>';
  const workflow=activity.workflow, children=activity.subagents||[], all=[...activity.agents,...children];
  const working=all.filter(a=>a.status==='working');
  const groups=[['Understand & plan',['interviewer','intelligence','architect','forecast','knowledge']],['Build & challenge',['implementation','test','differential','critic','adversarial','remediation']],['Protect & verify',['guardian','assurance','memory','cloud','stability','observability']]];
  const selected=all.find(a=>a.id===state.selectedAgent);
  return `<section class="agent-universe" aria-label="Live agent map">
    <div class="map-heading"><div><span class="eyeline">MISSION MAP</span><h2>${esc(activity.project_name)}</h2></div><span class="live-indicator"><i></i>Live · every 2s</span></div>
    <p class="activity-connection" role="status"></p>
    <div class="mission-ribbon"><span><b>${activity.counts.working}</b> working</span><span><b>${children.length}</b> subagents</span><span><b>${workflow.remaining}</b> steps remaining</span><span class="mission-completion">${workflow.completed}/${workflow.total} complete</span></div>
    <progress class="map-progress" value="${workflow.completed}" max="${workflow.total}" aria-label="${esc(workflow.title)} completed steps"></progress>
    <div class="map-caption"><span>${esc(workflow.title)}</span><span>${working.length?esc(working.map(a=>a.name).join(', '))+' working':!workflow.current_contract?'Outdated contract':workflow.remaining===0?'Workflow complete':({queued:'Queued for a worker',paused:'Paused',failed:'Review needs attention',interrupted:'Worker interrupted',cancelled:'Cancelled'}[workflow.status]||'Awaiting the next action')}</span></div>
    ${!workflow.current_contract?'<div class="callout">Historical review · the requirements changed. Start a new review for the current contract.</div>':''}
    <div class="robot-map">
      <div class="command-node">${mapNode(activity.agents.find(a=>a.id==='orchestrator'))}<div class="shared-context"><span class="context-orbit"></span><b>Shared mission context</b><span>One pinned requirements contract</span><small>${children.length?children.length+' bounded child assignments · one level deep':'Delegation available for requirements review'}</small></div></div>
      ${children.length?`<div class="child-branch"><span class="branch-label">DELEGATED BY ORCHESTRATOR</span><div class="child-nodes">${children.map(a=>mapNode(a,true)).join('')}</div></div>`:''}
      <div class="specialist-branches">${groups.map(([label,ids])=>`<section class="map-branch"><h3>${label}</h3><div class="branch-nodes">${ids.map(id=>mapNode(activity.agents.find(a=>a.id===id))).join('')}</div></section>`).join('')}</div>
    </div>
    <p class="map-legend"><span class="legend-working">● Working</span><span>○ Waiting / idle</span><span>✓ Completed</span><span>Dim robots: executor not configured</span><span>Select a robot to inspect its assignment</span></p>
    ${selected?`<div class="assignment-detail"><div>${robotIcon(selected.role||selected.id)}</div><div><span class="eyeline">${selected.parent_id?'CHILD OF MIGRATION ORCHESTRATOR':'SPECIALIST ASSIGNMENT'}</span><h3>${esc(selected.name)}</h3><p>${esc(selected.task)}</p><span class="hint">${esc(selected.mode)} · ${esc(agentStateLabel(selected.status))}${selected.context?' · '+esc(selected.context):''}</span>${selected.reason?`<p class="hint">${esc(selected.reason)}</p>`:''}</div></div>`:''}
    <details class="map-checkpoints"><summary>Flight plan · ${workflow.remaining} steps remaining</summary><ol class="workflow-steps">${workflow.steps.map((step,index)=>`<li class="workflow-step step-${esc(step.status)}"><span class="step-number">${step.status==='completed'?'✓':index+1}</span><div><strong>${esc(step.label)}</strong><span>${esc(agentStateLabel(step.status))}</span></div></li>`).join('')}</ol><p class="hint">Next: ${esc(workflow.next_step)}</p></details>
    <p class="activity-scope">${esc(workflow.detail)} Full migration steps are not yet defined. Robots represent role handlers; child counts represent actual assignments.</p>
    ${compact?`<div class="activity-footer">${button('Open mission workspace →','view','data-view="Agent operations"')}</div>`:''}
  </section>`;
}
function paintActivity() {
  const container=document.querySelector('#agent-activity');
  if(container){const focused=container.contains(document.activeElement)?document.activeElement.dataset.agent:null;const expanded=container.querySelector('.map-checkpoints')?.open;container.innerHTML=activityPanel(state.view==='Mission control');if(expanded)container.querySelector('.map-checkpoints').open=true;if(focused){const node=[...container.querySelectorAll('[data-agent]')].find(el=>el.dataset.agent===focused);node?.focus({preventScroll:true});}}
}
function markActivityDisconnected() {
  const container=document.querySelector('#agent-activity');
  if(!container)return;
  container.classList.add('activity-disconnected');
  const message=container.querySelector('.activity-connection');
  if(message)message.textContent='Connection interrupted. Showing the last recorded activity.';
  const live=container.querySelector('.live-indicator');
  if(live)live.textContent='Updates disconnected';
}
