// 通过 GitHub Git Data API 创建提交（直连 github.com 被阻断时的备用通道）
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPO = 'bogankung-eng/ashare-board';
const BRANCH = 'main';
const MESSAGE = 'auto: 每日看板更新 2026-09-08';
const FILES = ['board.html', 'public/index.html'];
const LOCAL_PARENT = 'ee659840e7186ea5825e7116315c82eec11b8593'; // 已知远端 HEAD

function getToken() {
  const out = execFileSync('git', ['credential', 'fill'], {
    input: 'protocol=https\nhost=github.com\n\n',
    encoding: 'utf8',
  });
  const m = out.match(/^password=(.+)$/m);
  if (!m) throw new Error('no token found');
  return m[1].trim();
}

async function main() {
  const token = getToken();
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/json',
    'User-Agent': 'ashare-board-auto',
  };
  const api = (p) => `https://api.github.com/repos/${REPO}/${p}`;

  // 1. 确认远端 HEAD 仍是我们已知的 parent
  const refRes = await fetch(api(`git/ref/heads/${BRANCH}`), { headers });
  if (!refRes.ok) throw new Error(`ref fetch failed: ${refRes.status}`);
  const ref = await refRes.json();
  const remoteSha = ref.object.sha;
  if (remoteSha !== LOCAL_PARENT) {
    throw new Error(`远端 HEAD 已变化 (${remoteSha.slice(0, 8)})，与预期 parent (${LOCAL_PARENT.slice(0, 8)}) 不符，中止`);
  }

  // 2. 获取 base tree
  const commitRes = await fetch(api(`git/commits/${remoteSha}`), { headers });
  if (!commitRes.ok) throw new Error(`base commit fetch failed: ${commitRes.status}`);
  const baseCommit = await commitRes.json();
  const baseTree = baseCommit.tree.sha;

  // 3. 创建 blobs
  const treeItems = [];
  for (const f of FILES) {
    const content = fs.readFileSync(path.resolve(__dirname, f));
    const blobRes = await fetch(api('git/blobs'), {
      method: 'POST', headers,
      body: JSON.stringify({ content: content.toString('base64'), encoding: 'base64' }),
    });
    if (!blobRes.ok) throw new Error(`blob create failed for ${f}: ${blobRes.status} ${await blobRes.text()}`);
    const blob = await blobRes.json();
    treeItems.push({ path: f, mode: '100644', type: 'blob', sha: blob.sha });
    console.log(`blob OK ${f}`);
  }

  // 4. 创建 tree
  const treeRes = await fetch(api('git/trees'), {
    method: 'POST', headers,
    body: JSON.stringify({ base_tree: baseTree, tree: treeItems }),
  });
  if (!treeRes.ok) throw new Error(`tree create failed: ${treeRes.status} ${await treeRes.text()}`);
  const newTree = await treeRes.json();
  console.log(`tree OK ${newTree.sha.slice(0, 8)}`);

  // 5. 创建 commit
  const newCommitRes = await fetch(api('git/commits'), {
    method: 'POST', headers,
    body: JSON.stringify({ message: MESSAGE, tree: newTree.sha, parents: [remoteSha] }),
  });
  if (!newCommitRes.ok) throw new Error(`commit create failed: ${newCommitRes.status} ${await newCommitRes.text()}`);
  const newCommit = await newCommitRes.json();
  console.log(`commit OK ${newCommit.sha.slice(0, 8)}`);

  // 6. 更新 ref
  const updRes = await fetch(api(`git/refs/heads/${BRANCH}`), {
    method: 'PATCH', headers,
    body: JSON.stringify({ sha: newCommit.sha, force: false }),
  });
  if (!updRes.ok) throw new Error(`ref update failed: ${updRes.status} ${await updRes.text()}`);
  console.log(`ref OK -> main = ${newCommit.sha}`);
}

main().catch((e) => { console.error('ERROR:', e.message); process.exit(1); });
