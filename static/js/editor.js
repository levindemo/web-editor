// 初始化Ace编辑器
const editor = ace.edit("editor");
editor.setTheme("ace/theme/dracula");
editor.session.setMode("ace/mode/python");
editor.setOptions({
    fontSize: "14px",
    tabSize: 4,
    useSoftTabs: true,
    showPrintMargin: false,
    wrap: true
});

// 设置示例代码
const exampleCode = `# Python Web Editor
# Write your code here and click Run

def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))

    # Try some calculations
    x = 42
    y = 13
    print(f"{x} + {y} = {x + y}")
    print(f"{x} * {y} = {x * y}")
`;
editor.setValue(exampleCode, 1);

// 获取DOM元素
const runBtn = document.getElementById('run-btn');
const clearBtn = document.getElementById('clear-btn');
const outputDiv = document.getElementById('output');
const statusDiv = document.getElementById('status');
const themeToggle = document.getElementById('theme-toggle');
const helpBtn = document.getElementById('help-btn');
const helpModal = document.getElementById('help-modal');
const closeHelp = document.getElementById('close-help');

// 运行代码
runBtn.addEventListener('click', async () => {
    const code = editor.getValue();

    if (!code.trim()) {
        outputDiv.innerHTML = "Error: No code to execute";
        return;
    }

    // 更新UI状态
    runBtn.disabled = true;
    runBtn.innerHTML = '<div class="loading mr-1"></div> Running...';
    outputDiv.innerHTML = "Executing code...";
    statusDiv.textContent = "Executing code...";

    try {
        // 发送代码到后端执行
        const response = await fetch('/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code })
        });

        const result = await response.json();

        // 显示结果
        if (result.success) {
            outputDiv.textContent = result.output || "No output";
            statusDiv.textContent = "Execution completed successfully";
        } else {
            outputDiv.textContent = result.output || "Unknown error";
            statusDiv.textContent = "Execution failed";
        }

    } catch (error) {
        outputDiv.textContent = `Error: ${error.message}`;
        statusDiv.textContent = "Error communicating with server";
    } finally {
        // 恢复UI状态
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="fa fa-play mr-1"></i> Run';
    }
});

// 清空编辑器
clearBtn.addEventListener('click', () => {
    editor.setValue('');
    outputDiv.innerHTML = "Editor cleared. Ready to write new code.";
    statusDiv.textContent = "Ready";
});

// 主题切换
let darkMode = false;
themeToggle.addEventListener('click', () => {
    darkMode = !darkMode;
    document.body.classList.toggle('dark-mode', darkMode);

    if (darkMode) {
        editor.setTheme("ace/theme/monokai");
        themeToggle.innerHTML = '<i class="fa fa-sun-o"></i>';
    } else {
        editor.setTheme("ace/theme/dracula");
        themeToggle.innerHTML = '<i class="fa fa-moon-o"></i>';
    }
});

// 帮助模态框
helpBtn.addEventListener('click', () => {
    helpModal.classList.remove('hidden');
});

closeHelp.addEventListener('click', () => {
    helpModal.classList.add('hidden');
});

// 点击模态框外部关闭
helpModal.addEventListener('click', (e) => {
    if (e.target === helpModal) {
        helpModal.classList.add('hidden');
    }
});

// 健康检查
setInterval(async () => {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        if (data.status === 'healthy') {
            // 仅在状态不是执行中时更新
            if (!statusDiv.textContent.includes('Executing')) {
                statusDiv.textContent = `Ready - ${data.containers} active container(s)`;
            }
        } else {
            statusDiv.textContent = "Server status: unhealthy";
        }
    } catch (error) {
        statusDiv.textContent = "Server unreachable";
    }
}, 10000);
