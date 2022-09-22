import { JSONEditor } from "vanilla-jsoneditor";
import * as rpc from 'vscode-ws-jsonrpc'


const tableBody = document.getElementById('table-body')
const tableRowTemplate: HTMLTemplateElement = <HTMLTemplateElement>document.getElementById('table-row')
const viewButtonTemplate: HTMLTemplateElement = <HTMLTemplateElement>document.getElementById('view-button')

const jsonViewer = new JSONEditor({
    target: <HTMLElement>document.getElementById('json-viewer'),
    props: {
        // readOnly: true
    }
})

/**
 * Represents a LSP protocol message, as captured by the agent.
 */
interface LSPMessage {
    session: string,
    timestamp: number,
    source: string,
    id?: string,
    method?: string,
    params?: any,
    result?: any,
    error?: any,
}


function addRow(message: LSPMessage) {
    const rowContainer = <DocumentFragment>tableRowTemplate.content.cloneNode(true)
    let cells = rowContainer.querySelectorAll('td')

    let ts = new Date(message.timestamp * 1000)

    cells[0].textContent = `${ts.toLocaleTimeString()}.${ts.getMilliseconds()}`
    cells[1].textContent = `${message.source}`
    cells[2].textContent = message.id ? `${message.id}` : ''
    cells[3].textContent = message.method ? `${message.method}` : ''

    if (message.params) {
        const fragment = <DocumentFragment>viewButtonTemplate.content.cloneNode(true)
        const button = <HTMLButtonElement>fragment.querySelector('button')

        button.addEventListener('click', (event) => {
            jsonViewer.set({ json: message.params })
        })

        cells[4].appendChild(button)
    }

    if (message.result) {
        const fragment = <DocumentFragment>viewButtonTemplate.content.cloneNode(true)
        const button = <HTMLButtonElement>fragment.querySelector('button')

        button.addEventListener('click', (event) => {
            jsonViewer.set({ json: message.result })
        })

        cells[5].appendChild(button)
    }

    if (message.error) {
        const fragment = <DocumentFragment>viewButtonTemplate.content.cloneNode(true)
        const button = <HTMLButtonElement>fragment.querySelector('button')

        button.addEventListener('click', (event) => {
            jsonViewer.set({ json: message.error })
        })

        cells[6].appendChild(button)
    }

    tableBody?.appendChild(rowContainer)
}

rpc.listen({
    webSocket: new WebSocket('ws://localhost:8765'),
    onConnection: (connection: rpc.MessageConnection) => {
        let notification = new rpc.NotificationType<LSPMessage>('$/lspMessage')
        connection.onNotification(notification, (params: LSPMessage) => {
            addRow(params)
        })
        connection.listen()
    }
})
