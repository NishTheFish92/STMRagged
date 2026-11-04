# Handover: STM32F4 documentation RAG

For Nishant, or a Claude Code session in the project's repo. This brief says **what** to build, **why**, and what makes the results trustworthy. **How** to build it is deliberately left out: researching the options and making the design calls is part of the challenge.

*Last updated: 2026-11-04*

---

## What and why

A question-answering system over the STM32F4 reference manual (RM0090). It answers with citations to page, and says "the docs don't cover this" when they don't.

The project exists for its **eval numbers and failure analysis**, not the demo. It has two phases, and each one ends with a resume update:

1. **Phase 1: RAG, built and validated.** Resume bullet v1. NotesAssistant comes off the resume.
2. **Phase 2: an agent, plus the comparison.** An agent that finds answers by navigating the indexed docs, compared with RAG and long context. Resume bullet v2.

Phase 2 starts only once Phase 1 is done.

## Fixed decisions (don't reopen without a reason)

| Area | Decision |
|---|---|
| Corpus | **RM0090 only** (reference manual for STM32F405/415, F407/417, F427/437, F429/439). Pinned to one revision and hash in a manifest. A download script goes in git, never the PDF (licensing) |
| Target audience | Firmware developers, students, and hardware designers choosing chips. This is who the system serves, not a multi-user feature. The golden set has questions from all three, and results are reported per audience |
| Output | **Answers only.** Register names, values and procedures, in prose. No code generation |
| LLM | `gemini-3.5-flash-lite`, served by freeLLMAPI through LangChain's OpenAI-compatible client. The same pinned model for every eval run, and for Phase 2 (it must support tool calling). Credentials live in `.env`, which is never read or committed |
| Framework | Python + LangChain |
| Rest of the stack | Not fixed yet (vector store, embeddings, retrievers, interface). Decide while building and record each choice and the reason in the README |
| Real users | None for now |

## The questions this project answers

- **Phase 1:** How well does RAG answer questions over RM0090, broken down by question type and audience? Where does it fail, and why?
- **Phase 2:** When does an agent navigating the indexed docs beat one-shot retrieval, and when does it lose? How much does the depth of indexing decide how well the agent finds things? Compare RAG, the agent and long context on accuracy, cost and latency.

Be ready to answer "why not just paste the docs into a long-context model?" with your own numbers by the end of Phase 2.

## Rules that make the numbers trustworthy (both phases)

1. **You write or verify every golden-set question against the PDF.** An LLM may suggest candidates, but each one gets checked and edited by you, and its provenance is recorded. Questions an LLM wrote without your review mostly test the LLM.
2. **Include questions the docs can't answer**, and score refusals both ways: refusing when it should, and wrongly refusing when the answer is there. A confident answer that isn't in the docs is the worst failure.
3. **Label the correct evidence by page**, never by chunk or by anything specific to how the system works. Then labels survive design changes, and RAG and the agent can be scored on the same set.
4. **Hold out a test split.** Tune on dev only, and run test only to report final numbers.
5. **Check any LLM judge against your own hand labels** on a sample before trusting it, and report how often they agree.
6. **Report results per question type and per audience,** not only averages. Groups are small, so don't over-read small differences.
7. **Make it reproducible:** pinned model, pinned corpus, and the config recorded with every result.
8. **Read the failures.** Tag the wrong answers by failure type. The README's "what failed and why" section comes from reading them, not from the scores.

## Done means

**Phase 1:**
- [ ] Golden set (about 60 questions covering all three audiences, with a dev/test split) and an eval harness that runs with one command
- [ ] Retrieval, answer-quality, refusal, cost and latency numbers, with the judge checked against your labels
- [ ] Failure analysis, plus one failure you found and fixed that you can talk about for 5 minutes
- [ ] A CLI to ask it questions. An MCP server can come later, only once the system is working
- [ ] README: architecture, key decisions and why, the results table, and what failed and why
- [ ] **Resume bullet v1, with measured numbers only.** NotesAssistant removed from the resume

**Phase 2:**
- [ ] An agent that answers from the same indexed corpus, run on the same golden set and test split
- [ ] A comparison of RAG, the agent and long context, by question type, on accuracy, evidence found, cost, latency, and how much the agent varies between runs
- [ ] What you found about how indexing depth affects the agent
- [ ] The agent's failure types, analysed like Phase 1's
- [ ] README updated with the comparison
- [ ] **Resume bullet v2**

## Out of scope

Code generation · multilingual · voice · fine-tuning · other ST documents (PM0214, datasheets, errata, app notes) and other chip families before Phase 1 is done · a polished UI · a real-user pilot

## After this project

Use the same eval approach on the Spotify agent (quick win #3 in [quick-wins.md](quick-wins.md)).
