<p align="center">
  <a href="https://mqleet.github.io/Switch-Swe/">
    <img src="assets/logo.svg" alt="Switch-SWE crossed-arrow logo" width="96" height="96">
  </a>
</p>

<h1 align="center">Switch-SWE</h1>

<p align="center">
  <strong>Do Coding Agents Hold Focus When Switching Between Unfinished Tasks?</strong>
</p>

<p align="center">
  <a href="https://mqleet.github.io/Switch-Swe/">
    <img src="https://img.shields.io/badge/Project-Page-b65334?style=flat&amp;logo=githubpages&amp;logoColor=white" alt="Project Page">
  </a>
  <a href="https://arxiv.org/abs/2611.02017">
    <img src="https://img.shields.io/badge/arXiv-2611.02017-B31B1B?style=flat&amp;logo=arxiv&amp;logoColor=white" alt="arXiv Paper">
  </a>
  <a href="https://huggingface.co/papers/2611.02017">
    <img src="https://img.shields.io/badge/HF-Daily%20Paper-FFD21E?style=flat&amp;logo=huggingface&amp;logoColor=FFD21E" alt="Hugging Face Daily Paper">
  </a>
</p>

<p align="center">
  <a href="https://github.com/harbor-framework/harbor">Harbor</a> ·
  <a href="plugins/context-manager">RCM plugin</a>
</p>

Switch-SWE evaluates how coding agents resume unfinished work after handling other tasks in the same repository. This release contains **200 switched sessions from 19 Python repositories**: **100 near** and **100 far**.

Each session interleaves five tasks in one continuous conversation, with a persistent checkout for each task. Near interruptions touch different source files sharing a parent directory; far interruptions touch different parent directories. Only the final focus-task changes are scored.

## Evaluate with Harbor

Requires Python 3.12+ and Docker. Install the pinned upstream Harbor:

```sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# All 200 tasks; choose your model.
harbor run -c harbor.yaml -a opencode -m <provider/model> --resume-trajectory

# One split or one task.
harbor run -p tasks/near -a opencode -m <provider/model> --resume-trajectory
harbor run -p tasks/far/sf076 -a opencode -m <provider/model> --resume-trajectory
```

Set your model provider's API key before running. `--resume-trajectory` keeps the same native agent session across requests; the included config enables it. Harbor builds the environments, executes the steps, transfers the final focus checkout, and runs the F2P/P2P tests in a separate verifier. Results are written to `jobs/`.

## Tasks

```text
tasks/near/    100 Harbor tasks
tasks/far/     100 Harbor tasks
```

Each task contains `task.toml`, an `environment/` build, ordered `steps/` with the original prompts, and final-step tests and a reference solution. Dependencies are pinned from the prepared environments and rebuilt from public packages. The reward is the final step's result.

[RCM](plugins/context-manager) contains the paper's OpenCode context-management plugin. [tools/](tools/) contains the dataset exporter and Harbor task checks.

Original code: [MIT](LICENSE). Included upstream source retains its original license notices.

## Citation

If you find Switch-SWE userful, please kindly cite our paper:

```bibtex
@misc{chang2026switchswe,
  title = {{Switch-SWE}: Do Coding Agents Hold Focus When Switching Between Unfinished Tasks?},
  author = {Shuochen Chang and Qianli Ma and Yibo Miao and Qingyang Liu and Bingjie Gao and Haonan Zhao and Siyu Sun and Yulin Sun and Han Zhao and Jiangtong Li},
  year = {2026},
  eprint = {2611.02017},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  url = {https://arxiv.org/abs/2611.02017}
}
```
