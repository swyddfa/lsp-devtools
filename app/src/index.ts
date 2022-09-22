import * as rpc from 'vscode-ws-jsonrpc'

rpc.listen({
    webSocket: new WebSocket('ws://localhost:8765'),
    onConnection: (connection: rpc.MessageConnection) => {
        let notification = new rpc.NotificationType<any>('$/lspMessage')
        connection.onNotification(notification, (params: any) => {
            console.log(params.method)
        })
        connection.listen()
    }
})
