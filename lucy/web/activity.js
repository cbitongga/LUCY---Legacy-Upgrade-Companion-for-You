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
const ACTIVITY_LABELS = {working:'Working now',waiting:'Waiting',completed:'Completed',failed:'Needs attention',paused:'Paused',interrupted:'Worker interrupted',cancelled:'Cancelled',stale:'Outdated',idle:'Idle',not_configured:'Not configured',pending:'Up next'};

function agentIcon(id) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${AGENT_GLYPHS[id] || AGENT_GLYPHS.orchestrator}</svg>`;
}

function agentStateLabel(status) {
  return ACTIVITY_LABELS[status] || 'Unknown';
}

function agentTile(agent) {
  return `<article class="agent-tile agent-${esc(agent.status)}">
    <div class="agent-tile-top"><span class="agent-avatar">${agentIcon(agent.id)}</span><span class="agent-state"><i></i>${esc(agentStateLabel(agent.status))}</span></div>
    <h3>${esc(agent.name)}</h3><p class="agent-assignment">${esc(agent.task)}</p><span class="agent-mode">${esc(agent.mode)}</span>
  </article>`;
}

function activityPanel(compact=false) {
  const activity=state.activity;
  if(!activity) return '<div class="card empty"><h2>Your engineering team is ready to meet you</h2><p>Create or open a project to see assignments and progress.</p></div>';
  const workflow=activity.workflow;
  const working=activity.agents.filter(a=>a.status==='working');
  const needsAttention=activity.counts.failed+activity.counts.interrupted;
  const ranks={working:0,failed:1,interrupted:1,paused:2,waiting:3,completed:4,stale:5,cancelled:6,idle:7,not_configured:8};
  const agents=[...activity.agents].sort((a,b)=>(ranks[a.status]??9)-(ranks[b.status]??9));
  const roster=compact?agents.slice(0,6):agents;
  const current=working.length?working.map(a=>a.name).join(', '):needsAttention?'A review needs attention':workflow.status==='queued'?'Queued for a worker':workflow.status==='paused'?'Work is paused':workflow.remaining===0&&workflow.current_contract?'Current workflow complete':'No agents executing right now';
  return `<section class="activity-board" aria-label="Agent activity and workflow progress">
    <div class="activity-heading"><div><span class="eyeline">TEAM ACTIVITY</span><h2>${esc(activity.project_name)}</h2></div><span class="live-indicator"><i></i>Updates every 2s</span></div>
    <p class="activity-connection" role="status"></p>
    <div class="activity-overview">
      <div class="work-now"><span class="label">Working now</span><strong>${activity.counts.working}</strong><p>${esc(current)}</p></div>
      <div class="workflow-summary"><div class="row"><h3>${esc(workflow.title)}</h3><span class="step-count">${workflow.completed} / ${workflow.total} complete</span></div>
        <progress value="${workflow.completed}" max="${workflow.total}" aria-label="Completed steps in ${esc(workflow.title)}"></progress>
        <div class="row"><strong>${workflow.remaining} ${workflow.remaining===1?'step':'steps'} remaining</strong><span class="hint">${activity.counts.waiting} agents waiting</span></div>
        <p class="hint">${esc(workflow.next_step)}</p>
      </div>
    </div>
    ${!workflow.current_contract?'<div class="callout">This review belongs to an older requirements contract. Its completion is historical, not progress on the current contract.</div>':''}
    <ol class="workflow-steps">${workflow.steps.map((step,index)=>`<li class="workflow-step step-${esc(step.status)}"><span class="step-number">${step.status==='completed'?'✓':index+1}</span><div><strong>${esc(step.label)}</strong><span>${esc(agentStateLabel(step.status))} · ${esc(step.agent_id?activity.agents.find(a=>a.id===step.agent_id)?.name:'You')}</span></div></li>`).join('')}</ol>
    <p class="activity-scope">${esc(workflow.detail)} <span>Full migration: remaining steps not yet defined.</span></p>
    <div class="roster-heading"><h3>${compact?'Assigned & available specialists':'All 18 specialists'}</h3><span class="hint">Animated icons indicate actual work · local handlers are labeled</span></div>
    <div class="agent-roster">${roster.map(agentTile).join('')}</div>
    ${compact?`<div class="activity-footer">${button('View all agents & progress →','view','data-view="Agent operations"')}<span class="hint">${activity.counts.not_configured} specialists await an executor</span></div>`:''}
  </section>`;
}

function paintActivity() {
  const container=document.querySelector('#agent-activity');
  if(container) container.innerHTML=activityPanel(state.view==='Mission control');
}

function markActivityDisconnected() {
  const container=document.querySelector('#agent-activity');
  if(!container) return;
  container.classList.add('activity-disconnected');
  const message=container.querySelector('.activity-connection');
  if(message) message.textContent='Live updates unavailable. Showing the last recorded state; activity may have changed.';
  const live=container.querySelector('.live-indicator');
  if(live) live.textContent='Updates disconnected';
}
