---
name: github-workflow
description: Structures github workflow practices. Use when planning code changes and proposing implementations to document the lifecycle of GitHub Issues.
---

# GitHub Workflow

## Overview

GitHub is our source of truth for project management. Issues document requested changes along with reasoning and context. Pull Requests (PR) represent a decision point with a human in the loop to review code and perform quality assurance before the proposed code is merged into the stable trunk.

## When to Use

ALWAYS. Every project that is associated with a GitHub repository should follow this workflow. It is the default for all new projects and is expected for all existing projects.

Whenever planning, use this skill to ensure every change is first documented in a GitHub Issue, that Issue is updated when the plan is revised to document the decision-making-process, and that the implementation of the change is submitted as a Pull Request while referencing the issue. This ensures that Issues act as a single source of truth.

## Core Principles

### Trunk-Based Development

Keep `main` always deployable. Work in short-lived feature branches that diverge from `main` and merge back quickly. This keeps the codebase healthy and reduces merge conflicts. Whether `main` is restricted to directly pushing or not, the principle is the same: keep `main` deployable at all times and all new work should be done in a dedicated branch that has been branched from main and is intended to be merged back into main without any conflicts, via the process of Pull Requests and code review.

#### Branch Naming

Keep branch names short, descriptive, and prefixed with the type of work being done. Use the following conventions (with examples):

```
feature/<short-description>   → feature/task-creation
fix/<short-description>       → fix/duplicate-tasks
chore/<short-description>     → chore/update-deps
refactor/<short-description>  → refactor/auth-module
```

### 1. Document plans in a GitHub Issue

The beginning of every change should initiate as a GitHub Issue. The issue should contain a clear description of the problem, the proposed solution, and any relevant context or references. This ensures that all stakeholders are aware of the change and can provide input before any code is written. If a plan is instigated without an explicit GitHub Issue identified, the human should be asked whether there is an existing GitHub Issue or if the agent should create one. 

Issues are identified by a unique number following the `#` symbol. For example, `#123` refers to issue number 123. However, the issue number should be validated to make sure it is a valid issue number in the repository. If the issue number is invalid, the human should be asked to provide a valid issue number or to choose for the agent to create a new issue. Issues can be retrieved via the GitHub API or by using the `gh` CLI tool. If a human is asked to provide an issue number, they should be prompted to provide the issue number in the format `#<issue-number>` where <issue-number> is the number of the GitHub Issue that the plan implements. GitHub Issues are also retrievable via the GitHub web interface, which can be accessed by navigating to the repository (e.g. https://github.com/<owner>/<repo>) with the issue identifier appended to the URL (e.g. /issues/<issue-number>); in the URL, replace all labels in tags (i.e. <tag>) with the appropriate values for the repository and issue number.

As plans are created and revised, the GitHub Issue should be updated with new comments to reflect the current state of the plan. Updated comments should accurately reflect the decisions including what an agent created, what input and decisions a human made, and what revisions were made. 

For example, if an agent creates a plan and a human provides feedback, the agent should update the GitHub Issue with a comment that verbatim quotes the feedback. If the agent asks a human to make a decision, quote the questions, the options provided, and the decisions made.

If a human prompts an agent that changes the direction of the plan, the agent should update the GitHub Issue with a comment that quotes the human's prompt (and attributes the quote to them), and then summarizes the decision and attributes the agent's changes in response to the human's prompt.

This ensures that all stakeholders are aware of the change's plan as well as decision-makers' thought process.

### 2. Pull Requests for Code Review

Pull Requests (PRs) are the mechanism for code review and quality assurance. Every implemented plan's code should be submitted as a PR, which should include a clear description of the change, any relevant context or references, as well as any known limitations or assumptions made. The PR should be reviewed by at least one human and only humans should approve the PR and merge it into `main`.

If a PR implements a plan that was documented in a GitHub Issue, the PR should reference the issue number in the description with the format `closes #<issue-number>` where <issue-number> is the number of the GitHub Issue that the PR implements. This ensures that all stakeholders are aware of the change and can provide input before any code is merged into `main`. The PR should be updated with a summary of the changes made, any relevant context or references, and any questions or concerns that need to be addressed.

If a PR is opened with any conflicts, the agent should be asked to resolve the conflicts before the PR can be merged. If the agent is unable to resolve the conflicts, the human should be asked to assist in resolving the conflicts via a comment in the PR.

If a code review or comments on a PR requests changes, the agent should continue to work on the same feature branch and make revisions according to the requested changes. The agent should not create a new branch for the same feature. The PR should be updated with a summary of the changes made, any relevant context or references, and any questions or concerns that need to be addressed.
