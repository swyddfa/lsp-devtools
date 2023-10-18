-- Dump the client capabilities for this version of neovim.
local version_info = vim.version()
local version = string.format('%d.%d.%d', version_info.major, version_info.minor, version_info.patch)

local params = {
    clientInfo = {
        name = 'Neovim',
        version = version,
    },
    capabilities = vim.lsp.protocol.make_client_capabilities(),
}

local json = vim.json.encode(params)
local bufnr = vim.api.nvim_create_buf(true, false)
vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, { json })

vim.api.nvim_buf_call(bufnr, function()
    vim.cmd(string.format(':w neovim_v%s.json', version))
    vim.cmd('.!python -m json.tool %')
    vim.cmd(':w')
end)
