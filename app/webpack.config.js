const path = require('path')

module.exports = {
    target: 'web',
    entry: './src/index.ts',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'index.js',
    },
    devtool: 'source-map',
    resolve: {
        extensions: ['.ts', '.js'],
        mainFields: ['module', 'main']
    },
    module: {
        rules: [
            {
                test: /.ts$/,
                exclude: /node_modules/,
                use: [{
                    loader: 'ts-loader',
                }]
            }
        ]
    }
}
