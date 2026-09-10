15 fully-warmed Bellows mailboxes (100% warmup, 50/day each) across the three *-faire.com domains — better-faire.com, other-faire.com, un-faire.com (5 each). That's
  ~750/day capacity; your 25-lead first wave doesn't stress it at all. (The api-toolkit is currently sitting on the unpushed wrapper-refresh branch, which is why this call
  worked — the design has to account for landing that.)

  I now have everything. Here's the design.

  ---
  Design: Thin Sender — First Live Wave (Foothold, 25 leads)

  1. Scope

  In: Push the 25 ready foothold 3-touch sequences from VALIDATION-multi-touch-20260527 into a single Smartlead campaign, send for real, manage replies manually.
  Out (deferred): Provisioner automation, webhook reply-halt service, multi-cohort orchestration, the full Wave Assembler. Volume/scaling cohorts.

  2. One-time manual setup in Smartlead UI (no code)

  Done by hand because editing a live sequence re-dispatches sent touches (R-008a) — hand-creation in DRAFT is the safe path.
  - Create campaign Bellows — Foothold — Wave 1.
  - 3-step sequence using per-lead custom variables (this is what lets unique bodies ride one template):
    - Step 1 — subject {{t1_subject}}, body {{t1_body}}, delay 0
    - Step 2 — reply in same thread, body {{t2_body}}, delay 14 days
    - Step 3 — reply in same thread, body {{t3_body}}, delay 21 days (≈day 35)
  - Attach mailboxes: 3–5 from one domain (recommend better-faire.com — its signature carried the address in the smoke test). Confirm each has the signature footer Bellows 
  / 1209 N Orange St / Wilmington, DE 19801 (CAN-SPAM physical address).
  - Compliance config: unsubscribe_text="{{unsubscribe}}" (bare token — C-5 locked; empty disables RFC 8058 headers), auto_pause_domain_leads_on_reply ON, ascending day
  delays.
  - Leave campaign in DRAFT.

  3. The only code: push_wave.py

  A ~150-line script (lives in bridge/, reuses existing Phase-3 units + bridge/config.py):
  1. Read lineage: status='sampled' AND push_status='pending', sample_run_id='VALIDATION-multi-touch-20260527', cohort foothold, leads with all of touches 1/2/3.
  2. Join brand_intelligence_unified.primary_email; apply the deliverable-email filter (drops the .css/placeholder junk).
  3. Dedup (lead_id, touch_number) keeping newest (Phase-3 carry-forward), default-deny jurisdiction.
  4. For each lead, add_leads_to_campaign with custom fields {t1_subject, t1_body, t2_body, t3_body} (t2/t3 subjects unneeded — replies auto-prefix "Re:").
  5. Write back push_status='pushed', smartlead_lead_id, pushed_at to lineage.
  - Idempotent (skips already-pushed), --dry-run, --limit N flags.

  4. Rollout sequence

  1. Render smoke (1 lead → a mailbox you control): push one lead targeting a test inbox, flip active, confirm custom-var bodies render, "Re:" threading works,
  List-Unsubscribe header + physical address present, custom-field length OK. ← proves the unique-body mechanism (the smoke-test 3359397 never tested this).
  2. Real smoke (3–5 real foothold leads): push, activate, eyeball deliverability/inbox placement over a day.
  3. Full wave (remaining ~20): push, activate.

  5. Reply-halt & compliance during ramp

  Smartlead native stop-on-reply pauses the rest of a lead's sequence automatically; you watch the inbox during ramp (25 leads is trivially watchable). Manual reply
  handling was always the ramp plan. Unsubscribe handled by Smartlead's {{unsubscribe}} link + List-Unsubscribe header.

  6. Dependency & branch hygiene

  - Fresh branch off main: feat/spec-c-thin-sender. Register in active-branches ledger.
  - Cherry-pick (not wholesale-merge) from feat/marketplace-snapshots: bridge/config.py, the Phase-3 core units actually used (eligibility, validators, suppression),
  config/smartlead.json, the smartlead fixtures. Per memory: never wholesale-merge that branch.
  - Land the api-toolkit wrapper (feat/spec-c-contract-refresh-2026-05-20) — needed for add_leads_to_campaign custom fields + compliance setters.
  - Verify in Supabase before run: push_status CHECK constraint allows 'pushed'; sql/34 suppression view applied (or skip suppression for wave 1 — it's empty pre-send
  anyway).

  7. Top risks

  - R1 — wrong/dead emails slip through → land in spam, hurt domain reputation. Mitigation: deliverable filter + the 1-lead render smoke + 3–5 real smoke before full wave.
  - R2 — custom-field length/count limit truncates a body → broken email. Mitigation: render smoke verifies; probe_smartlead.py already checks this.
  - R3 — compliance header missing (bare-token regression) → CAN-SPAM exposure. Mitigation: render smoke inspects raw headers before any real send.
  - R4 — reply fires an orphan touch → manual watch + native stop-on-reply during ramp.

  ---
  Does this match what you want? Two open choices I baked in as recommendations you can override: sender domain = better-faire.com (3–5 mailboxes), and cadence T1→day0, 
  T2→day14, T3→day35. If those are fine and the design looks right, I'll write it up as the spec and we move to the implementation plan.
