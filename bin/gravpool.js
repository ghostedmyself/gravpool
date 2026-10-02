#!/usr/bin/env node

const { execSync, spawn } = require('child_process');

function commandExists(cmd) {
    try {
        execSync(`${cmd} --version`, { stdio: 'ignore' });
        return true;
    } catch (e) {
        return false;
    }
}

function main() {
    const args = process.argv.slice(2);
    const hasUv = commandExists('uv');
    const hasPython3 = commandExists('python3');

    if (hasUv) {
        try {
            execSync('uv tool install gravpool --quiet', { stdio: 'inherit' });
        } catch (e) {
            // Might already be installed or fail silently
        }
        const child = spawn('uv', ['run', 'gravpool', ...args], { stdio: 'inherit' });
        child.on('exit', (code) => {
            process.exit(code !== null ? code : 1);
        });
    } else if (hasPython3) {
        let pipCmd = commandExists('pip3') ? 'pip3' : (commandExists('pip') ? 'pip' : null);
        if (pipCmd) {
            try {
                execSync(`${pipCmd} install gravpool --quiet`, { stdio: 'inherit' });
            } catch (e) {
                // Ignore silent errors
            }
            const child = spawn('python3', ['-m', 'gravpool', ...args], { stdio: 'inherit' });
            child.on('exit', (code) => {
                process.exit(code !== null ? code : 1);
            });
        } else {
            console.error('Error: Python 3 is installed but pip/pip3 could not be found.');
            console.error('Please install pip or use "uv" (https://docs.astral.sh/uv/getting-started/installation/).');
            process.exit(1);
        }
    } else {
        console.error('Error: Neither "uv" nor "python3" was found on this system.');
        console.error('Please install "uv" (recommended) or Python 3 to run gravpool.');
        process.exit(1);
    }
}

main();
