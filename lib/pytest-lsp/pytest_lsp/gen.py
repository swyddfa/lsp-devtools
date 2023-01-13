# GENERATED FROM scripts/gen-client.py -- DO NOT EDIT
# Last Modified: 2023-01-13 19:50:12.916971
# flake8: noqa
import lsprotocol.types
from lsprotocol.types import CallHierarchyIncomingCallsParams
from lsprotocol.types import CallHierarchyOutgoingCallsParams
from lsprotocol.types import CallHierarchyPrepareParams
from lsprotocol.types import CancelParams
from lsprotocol.types import CodeAction
from lsprotocol.types import CodeActionParams
from lsprotocol.types import CodeLens
from lsprotocol.types import CodeLensParams
from lsprotocol.types import ColorPresentationParams
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from lsprotocol.types import CreateFilesParams
from lsprotocol.types import CreateFilesParams
from lsprotocol.types import DeclarationParams
from lsprotocol.types import DefinitionParams
from lsprotocol.types import DeleteFilesParams
from lsprotocol.types import DeleteFilesParams
from lsprotocol.types import DidChangeConfigurationParams
from lsprotocol.types import DidChangeNotebookDocumentParams
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidChangeWatchedFilesParams
from lsprotocol.types import DidChangeWorkspaceFoldersParams
from lsprotocol.types import DidCloseNotebookDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenNotebookDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveNotebookDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import DocumentColorParams
from lsprotocol.types import DocumentDiagnosticParams
from lsprotocol.types import DocumentFormattingParams
from lsprotocol.types import DocumentHighlightParams
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import DocumentOnTypeFormattingParams
from lsprotocol.types import DocumentRangeFormattingParams
from lsprotocol.types import DocumentSymbolParams
from lsprotocol.types import ExecuteCommandParams
from lsprotocol.types import FoldingRangeParams
from lsprotocol.types import HoverParams
from lsprotocol.types import ImplementationParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import InitializedParams
from lsprotocol.types import InlayHint
from lsprotocol.types import InlayHintParams
from lsprotocol.types import InlineValueParams
from lsprotocol.types import LinkedEditingRangeParams
from lsprotocol.types import MonikerParams
from lsprotocol.types import PrepareRenameParams
from lsprotocol.types import ProgressParams
from lsprotocol.types import ReferenceParams
from lsprotocol.types import RenameFilesParams
from lsprotocol.types import RenameFilesParams
from lsprotocol.types import RenameParams
from lsprotocol.types import SelectionRangeParams
from lsprotocol.types import SemanticTokensDeltaParams
from lsprotocol.types import SemanticTokensParams
from lsprotocol.types import SemanticTokensRangeParams
from lsprotocol.types import SetTraceParams
from lsprotocol.types import SignatureHelpParams
from lsprotocol.types import TypeDefinitionParams
from lsprotocol.types import TypeHierarchyPrepareParams
from lsprotocol.types import TypeHierarchySubtypesParams
from lsprotocol.types import TypeHierarchySupertypesParams
from lsprotocol.types import WillSaveTextDocumentParams
from lsprotocol.types import WillSaveTextDocumentParams
from lsprotocol.types import WorkDoneProgressCancelParams
from lsprotocol.types import WorkspaceDiagnosticParams
from lsprotocol.types import WorkspaceSymbol
from lsprotocol.types import WorkspaceSymbolParams
from pygls.server import Server
import typing


class Client(Server):
    """Used to drive the language server under test."""

    async def call_hierarchy_incoming_calls_request(self, params: CallHierarchyIncomingCallsParams) -> typing.Optional[typing.List[lsprotocol.types.CallHierarchyIncomingCall]]:
        """Make a ``callHierarchy/incomingCalls`` request.

        A request to resolve the incoming calls for a given `CallHierarchyItem`.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("callHierarchy/incomingCalls", params)

    async def call_hierarchy_outgoing_calls_request(self, params: CallHierarchyOutgoingCallsParams) -> typing.Optional[typing.List[lsprotocol.types.CallHierarchyOutgoingCall]]:
        """Make a ``callHierarchy/outgoingCalls`` request.

        A request to resolve the outgoing calls for a given `CallHierarchyItem`.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("callHierarchy/outgoingCalls", params)

    async def code_action_resolve_request(self, params: CodeAction) -> lsprotocol.types.CodeAction:
        """Make a ``codeAction/resolve`` request.

        Request to resolve additional information for a given code action.The
        request's parameter is of type CodeAction the response is of type
        CodeAction or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("codeAction/resolve", params)

    async def code_lens_resolve_request(self, params: CodeLens) -> lsprotocol.types.CodeLens:
        """Make a ``codeLens/resolve`` request.

        A request to resolve a command for a given code lens.
        """
        return await self.lsp.send_request_async("codeLens/resolve", params)

    async def completion_item_resolve_request(self, params: CompletionItem) -> lsprotocol.types.CompletionItem:
        """Make a ``completionItem/resolve`` request.

        Request to resolve additional information for a given completion
        item.The request's parameter is of type CompletionItem the response is of
        type CompletionItem or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("completionItem/resolve", params)

    async def document_link_resolve_request(self, params: DocumentLink) -> lsprotocol.types.DocumentLink:
        """Make a ``documentLink/resolve`` request.

        Request to resolve additional information for a given document link.

        The request's parameter is of type DocumentLink the response is of
        type DocumentLink or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("documentLink/resolve", params)

    async def initialize_request(self, params: InitializeParams) -> lsprotocol.types.InitializeResult:
        """Make a ``initialize`` request.

        The initialize request is sent from the client to the server.

        It is sent once as the request after starting up the server. The
        requests parameter is of type InitializeParams the response if of
        type InitializeResult of a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("initialize", params)

    async def inlay_hint_resolve_request(self, params: InlayHint) -> lsprotocol.types.InlayHint:
        """Make a ``inlayHint/resolve`` request.

        A request to resolve additional properties for an inlay hint. The
        request's parameter is of type InlayHint, the response is of type InlayHint
        or a Thenable that resolves to such.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("inlayHint/resolve", params)

    async def shutdown_request(self, params: None) -> None:
        """Make a ``shutdown`` request.

        A shutdown request is sent from the client to the server.

        It is sent once when the client decides to shutdown the server. The
        only notification that is sent after a shutdown request is the exit
        event.
        """
        return await self.lsp.send_request_async("shutdown", params)

    async def text_document_code_action_request(self, params: CodeActionParams) -> typing.Optional[typing.List[typing.Union[lsprotocol.types.Command, lsprotocol.types.CodeAction]]]:
        """Make a ``textDocument/codeAction`` request.

        A request to provide commands for the given text document and range.
        """
        return await self.lsp.send_request_async("textDocument/codeAction", params)

    async def text_document_code_lens_request(self, params: CodeLensParams) -> typing.Optional[typing.List[lsprotocol.types.CodeLens]]:
        """Make a ``textDocument/codeLens`` request.

        A request to provide code lens for the given text document.
        """
        return await self.lsp.send_request_async("textDocument/codeLens", params)

    async def text_document_color_presentation_request(self, params: ColorPresentationParams) -> typing.List[lsprotocol.types.ColorPresentation]:
        """Make a ``textDocument/colorPresentation`` request.

        A request to list all presentation for a color.

        The request's parameter is of type ColorPresentationParams the
        response is of type ColorInformation[] or a Thenable that resolves
        to such.
        """
        return await self.lsp.send_request_async("textDocument/colorPresentation", params)

    async def text_document_completion_request(self, params: CompletionParams) -> typing.Union[typing.List[lsprotocol.types.CompletionItem], lsprotocol.types.CompletionList, None]:
        """Make a ``textDocument/completion`` request.

        Request to request completion at a given text document position. The
        request's parameter is of type TextDocumentPosition the response is of type
        CompletionItem[] or CompletionList or a Thenable that resolves to such.

        The request can delay the computation of the
        [`detail`](#CompletionItem.detail) and
        [`documentation`](#CompletionItem.documentation) properties to the
        `completionItem/resolve` request. However, properties that are
        needed for the initial sorting and filtering, like `sortText`,
        `filterText`, `insertText`, and `textEdit`, must not be changed
        during resolve.
        """
        return await self.lsp.send_request_async("textDocument/completion", params)

    async def text_document_declaration_request(self, params: DeclarationParams) -> typing.Union[lsprotocol.types.Location, typing.List[lsprotocol.types.Location], typing.List[lsprotocol.types.LocationLink], None]:
        """Make a ``textDocument/declaration`` request.

        A request to resolve the type definition locations of a symbol at a
        given text document position.

        The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type Declaration or
        a typed array of DeclarationLink or a Thenable that resolves to
        such.
        """
        return await self.lsp.send_request_async("textDocument/declaration", params)

    async def text_document_definition_request(self, params: DefinitionParams) -> typing.Union[lsprotocol.types.Location, typing.List[lsprotocol.types.Location], typing.List[lsprotocol.types.LocationLink], None]:
        """Make a ``textDocument/definition`` request.

        A request to resolve the definition location of a symbol at a given text
        document position.

        The request's parameter is of type [TextDocumentPosition]
        (#TextDocumentPosition) the response is of either type Definition or
        a typed array of DefinitionLink or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/definition", params)

    async def text_document_diagnostic_request(self, params: DocumentDiagnosticParams) -> typing.Union[lsprotocol.types.RelatedFullDocumentDiagnosticReport, lsprotocol.types.RelatedUnchangedDocumentDiagnosticReport]:
        """Make a ``textDocument/diagnostic`` request.

        The document diagnostic request definition.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("textDocument/diagnostic", params)

    async def text_document_document_color_request(self, params: DocumentColorParams) -> typing.List[lsprotocol.types.ColorInformation]:
        """Make a ``textDocument/documentColor`` request.

        A request to list all color symbols found in a given text document.

        The request's parameter is of type DocumentColorParams the response
        is of type ColorInformation[] or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/documentColor", params)

    async def text_document_document_highlight_request(self, params: DocumentHighlightParams) -> typing.Optional[typing.List[lsprotocol.types.DocumentHighlight]]:
        """Make a ``textDocument/documentHighlight`` request.

        Request to resolve a DocumentHighlight for a given text document
        position.

        The request's parameter is of type [TextDocumentPosition]
        (#TextDocumentPosition) the request response is of type
        [DocumentHighlight[]] (#DocumentHighlight) or a Thenable that
        resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/documentHighlight", params)

    async def text_document_document_link_request(self, params: DocumentLinkParams) -> typing.Optional[typing.List[lsprotocol.types.DocumentLink]]:
        """Make a ``textDocument/documentLink`` request.

        A request to provide document links.
        """
        return await self.lsp.send_request_async("textDocument/documentLink", params)

    async def text_document_document_symbol_request(self, params: DocumentSymbolParams) -> typing.Union[typing.List[lsprotocol.types.SymbolInformation], typing.List[lsprotocol.types.DocumentSymbol], None]:
        """Make a ``textDocument/documentSymbol`` request.

        A request to list all symbols found in a given text document.

        The request's parameter is of type TextDocumentIdentifier the
        response is of type SymbolInformation[] or a Thenable that resolves
        to such.
        """
        return await self.lsp.send_request_async("textDocument/documentSymbol", params)

    async def text_document_folding_range_request(self, params: FoldingRangeParams) -> typing.Optional[typing.List[lsprotocol.types.FoldingRange]]:
        """Make a ``textDocument/foldingRange`` request.

        A request to provide folding ranges in a document.

        The request's parameter is of type FoldingRangeParams, the response
        is of type FoldingRangeList or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/foldingRange", params)

    async def text_document_formatting_request(self, params: DocumentFormattingParams) -> typing.Optional[typing.List[lsprotocol.types.TextEdit]]:
        """Make a ``textDocument/formatting`` request.

        A request to to format a whole document.
        """
        return await self.lsp.send_request_async("textDocument/formatting", params)

    async def text_document_hover_request(self, params: HoverParams) -> typing.Optional[lsprotocol.types.Hover]:
        """Make a ``textDocument/hover`` request.

        Request to request hover information at a given text document position.

        The request's parameter is of type TextDocumentPosition the response
        is of type Hover or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/hover", params)

    async def text_document_implementation_request(self, params: ImplementationParams) -> typing.Union[lsprotocol.types.Location, typing.List[lsprotocol.types.Location], typing.List[lsprotocol.types.LocationLink], None]:
        """Make a ``textDocument/implementation`` request.

        A request to resolve the implementation locations of a symbol at a given
        text document position.

        The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type Definition or
        a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/implementation", params)

    async def text_document_inlay_hint_request(self, params: InlayHintParams) -> typing.Optional[typing.List[lsprotocol.types.InlayHint]]:
        """Make a ``textDocument/inlayHint`` request.

        A request to provide inlay hints in a document. The request's parameter
        is of type InlayHintsParams, the response is of type.

        [InlayHint[]](#InlayHint[]) or a Thenable that resolves to such.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("textDocument/inlayHint", params)

    async def text_document_inline_value_request(self, params: InlineValueParams) -> typing.Optional[typing.List[typing.Union[lsprotocol.types.InlineValueText, lsprotocol.types.InlineValueVariableLookup, lsprotocol.types.InlineValueEvaluatableExpression]]]:
        """Make a ``textDocument/inlineValue`` request.

        A request to provide inline values in a document. The request's
        parameter is of type InlineValueParams, the response is of type.

        [InlineValue[]](#InlineValue[]) or a Thenable that resolves to such.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("textDocument/inlineValue", params)

    async def text_document_linked_editing_range_request(self, params: LinkedEditingRangeParams) -> typing.Optional[lsprotocol.types.LinkedEditingRanges]:
        """Make a ``textDocument/linkedEditingRange`` request.

        A request to provide ranges that can be edited together.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("textDocument/linkedEditingRange", params)

    async def text_document_moniker_request(self, params: MonikerParams) -> typing.Optional[typing.List[lsprotocol.types.Moniker]]:
        """Make a ``textDocument/moniker`` request.

        A request to get the moniker of a symbol at a given text document
        position.

        The request parameter is of type TextDocumentPositionParams. The
        response is of type [Moniker[]](#Moniker[]) or `null`.
        """
        return await self.lsp.send_request_async("textDocument/moniker", params)

    async def text_document_on_type_formatting_request(self, params: DocumentOnTypeFormattingParams) -> typing.Optional[typing.List[lsprotocol.types.TextEdit]]:
        """Make a ``textDocument/onTypeFormatting`` request.

        A request to format a document on type.
        """
        return await self.lsp.send_request_async("textDocument/onTypeFormatting", params)

    async def text_document_prepare_call_hierarchy_request(self, params: CallHierarchyPrepareParams) -> typing.Optional[typing.List[lsprotocol.types.CallHierarchyItem]]:
        """Make a ``textDocument/prepareCallHierarchy`` request.

        A request to result a `CallHierarchyItem` in a document at a given
        position. Can be used as an input to an incoming or outgoing call
        hierarchy.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("textDocument/prepareCallHierarchy", params)

    async def text_document_prepare_rename_request(self, params: PrepareRenameParams) -> typing.Union[lsprotocol.types.Range, lsprotocol.types.PrepareRenameResult_Type1, lsprotocol.types.PrepareRenameResult_Type2, None]:
        """Make a ``textDocument/prepareRename`` request.

        A request to test and perform the setup necessary for a rename.

        @since 3.16 - support for default behavior
        """
        return await self.lsp.send_request_async("textDocument/prepareRename", params)

    async def text_document_prepare_type_hierarchy_request(self, params: TypeHierarchyPrepareParams) -> typing.Optional[typing.List[lsprotocol.types.TypeHierarchyItem]]:
        """Make a ``textDocument/prepareTypeHierarchy`` request.

        A request to result a `TypeHierarchyItem` in a document at a given
        position. Can be used as an input to a subtypes or supertypes type
        hierarchy.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("textDocument/prepareTypeHierarchy", params)

    async def text_document_range_formatting_request(self, params: DocumentRangeFormattingParams) -> typing.Optional[typing.List[lsprotocol.types.TextEdit]]:
        """Make a ``textDocument/rangeFormatting`` request.

        A request to to format a range in a document.
        """
        return await self.lsp.send_request_async("textDocument/rangeFormatting", params)

    async def text_document_references_request(self, params: ReferenceParams) -> typing.Optional[typing.List[lsprotocol.types.Location]]:
        """Make a ``textDocument/references`` request.

        A request to resolve project-wide references for the symbol denoted by
        the given text document position.

        The request's parameter is of type ReferenceParams the response is
        of type Location[] or a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/references", params)

    async def text_document_rename_request(self, params: RenameParams) -> typing.Optional[lsprotocol.types.WorkspaceEdit]:
        """Make a ``textDocument/rename`` request.

        A request to rename a symbol.
        """
        return await self.lsp.send_request_async("textDocument/rename", params)

    async def text_document_selection_range_request(self, params: SelectionRangeParams) -> typing.Optional[typing.List[lsprotocol.types.SelectionRange]]:
        """Make a ``textDocument/selectionRange`` request.

        A request to provide selection ranges in a document.

        The request's parameter is of type SelectionRangeParams, the
        response is of type [SelectionRange[]](#SelectionRange[]) or a
        Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/selectionRange", params)

    async def text_document_semantic_tokens_full_request(self, params: SemanticTokensParams) -> typing.Optional[lsprotocol.types.SemanticTokens]:
        """Make a ``textDocument/semanticTokens/full`` request.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("textDocument/semanticTokens/full", params)

    async def text_document_semantic_tokens_full_delta_request(self, params: SemanticTokensDeltaParams) -> typing.Union[lsprotocol.types.SemanticTokens, lsprotocol.types.SemanticTokensDelta, None]:
        """Make a ``textDocument/semanticTokens/full/delta`` request.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("textDocument/semanticTokens/full/delta", params)

    async def text_document_semantic_tokens_range_request(self, params: SemanticTokensRangeParams) -> typing.Optional[lsprotocol.types.SemanticTokens]:
        """Make a ``textDocument/semanticTokens/range`` request.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("textDocument/semanticTokens/range", params)

    async def text_document_signature_help_request(self, params: SignatureHelpParams) -> typing.Optional[lsprotocol.types.SignatureHelp]:
        """Make a ``textDocument/signatureHelp`` request.


        """
        return await self.lsp.send_request_async("textDocument/signatureHelp", params)

    async def text_document_type_definition_request(self, params: TypeDefinitionParams) -> typing.Union[lsprotocol.types.Location, typing.List[lsprotocol.types.Location], typing.List[lsprotocol.types.LocationLink], None]:
        """Make a ``textDocument/typeDefinition`` request.

        A request to resolve the type definition locations of a symbol at a
        given text document position.

        The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type Definition or
        a Thenable that resolves to such.
        """
        return await self.lsp.send_request_async("textDocument/typeDefinition", params)

    async def text_document_will_save_wait_until_request(self, params: WillSaveTextDocumentParams) -> typing.Optional[typing.List[lsprotocol.types.TextEdit]]:
        """Make a ``textDocument/willSaveWaitUntil`` request.

        A document will save request is sent from the client to the server
        before the document is actually saved.

        The request can return an array of TextEdits which will be applied
        to the text document before it is saved. Please note that clients
        might drop results if computing the text edits took too long or if a
        server constantly fails on this request. This is done to keep the
        save fast and reliable.
        """
        return await self.lsp.send_request_async("textDocument/willSaveWaitUntil", params)

    async def type_hierarchy_subtypes_request(self, params: TypeHierarchySubtypesParams) -> typing.Optional[typing.List[lsprotocol.types.TypeHierarchyItem]]:
        """Make a ``typeHierarchy/subtypes`` request.

        A request to resolve the subtypes for a given `TypeHierarchyItem`.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("typeHierarchy/subtypes", params)

    async def type_hierarchy_supertypes_request(self, params: TypeHierarchySupertypesParams) -> typing.Optional[typing.List[lsprotocol.types.TypeHierarchyItem]]:
        """Make a ``typeHierarchy/supertypes`` request.

        A request to resolve the supertypes for a given `TypeHierarchyItem`.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("typeHierarchy/supertypes", params)

    async def workspace_diagnostic_request(self, params: WorkspaceDiagnosticParams) -> lsprotocol.types.WorkspaceDiagnosticReport:
        """Make a ``workspace/diagnostic`` request.

        The workspace diagnostic request definition.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("workspace/diagnostic", params)

    async def workspace_diagnostic_refresh_request(self, params: None) -> None:
        """Make a ``workspace/diagnostic/refresh`` request.

        The diagnostic refresh request definition.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("workspace/diagnostic/refresh", params)

    async def workspace_execute_command_request(self, params: ExecuteCommandParams) -> typing.Union[object, typing.List[typing.Union[object, typing.List[lsprotocol.types.LSPAny], str, int, float, bool, None]], str, int, float, bool, None]:
        """Make a ``workspace/executeCommand`` request.

        A request send from the client to the server to execute a command.

        The request might return a workspace edit which the client will
        apply to the workspace.
        """
        return await self.lsp.send_request_async("workspace/executeCommand", params)

    async def workspace_inlay_hint_refresh_request(self, params: None) -> None:
        """Make a ``workspace/inlayHint/refresh`` request.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("workspace/inlayHint/refresh", params)

    async def workspace_inline_value_refresh_request(self, params: None) -> None:
        """Make a ``workspace/inlineValue/refresh`` request.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("workspace/inlineValue/refresh", params)

    async def workspace_semantic_tokens_refresh_request(self, params: None) -> None:
        """Make a ``workspace/semanticTokens/refresh`` request.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("workspace/semanticTokens/refresh", params)

    async def workspace_symbol_request(self, params: WorkspaceSymbolParams) -> typing.Union[typing.List[lsprotocol.types.SymbolInformation], typing.List[lsprotocol.types.WorkspaceSymbol], None]:
        """Make a ``workspace/symbol`` request.

        A request to list project-wide symbols matching the query string given
        by the WorkspaceSymbolParams. The response is of type SymbolInformation[]
        or a Thenable that resolves to such.

        @since 3.17.0 - support for WorkspaceSymbol in the returned data. Clients
         need to advertise support for WorkspaceSymbols via the client capability
         `workspace.symbol.resolveSupport`.
        """
        return await self.lsp.send_request_async("workspace/symbol", params)

    async def workspace_symbol_resolve_request(self, params: WorkspaceSymbol) -> lsprotocol.types.WorkspaceSymbol:
        """Make a ``workspaceSymbol/resolve`` request.

        A request to resolve the range inside the workspace symbol's location.

        @since 3.17.0
        """
        return await self.lsp.send_request_async("workspaceSymbol/resolve", params)

    async def workspace_will_create_files_request(self, params: CreateFilesParams) -> typing.Optional[lsprotocol.types.WorkspaceEdit]:
        """Make a ``workspace/willCreateFiles`` request.

        The will create files request is sent from the client to the server
        before files are actually created as long as the creation is triggered from
        within the client.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("workspace/willCreateFiles", params)

    async def workspace_will_delete_files_request(self, params: DeleteFilesParams) -> typing.Optional[lsprotocol.types.WorkspaceEdit]:
        """Make a ``workspace/willDeleteFiles`` request.

        The did delete files notification is sent from the client to the server
        when files were deleted from within the client.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("workspace/willDeleteFiles", params)

    async def workspace_will_rename_files_request(self, params: RenameFilesParams) -> typing.Optional[lsprotocol.types.WorkspaceEdit]:
        """Make a ``workspace/willRenameFiles`` request.

        The will rename files request is sent from the client to the server
        before files are actually renamed as long as the rename is triggered from
        within the client.

        @since 3.16.0
        """
        return await self.lsp.send_request_async("workspace/willRenameFiles", params)

    def notify_cancel_request(self, params: CancelParams) -> None:
        """Send a ``$/cancelRequest`` notification.


        """
        self.lsp.notify("$/cancelRequest", params)

    def notify_exit(self, params: None) -> None:
        """Send a ``exit`` notification.

        The exit event is sent from the client to the server to ask the server
        to exit its process.
        """
        self.lsp.notify("exit", params)

    def notify_initialized(self, params: InitializedParams) -> None:
        """Send a ``initialized`` notification.

        The initialized notification is sent from the client to the server after
        the client is fully initialized and the server is allowed to send requests
        from the server to the client.
        """
        self.lsp.notify("initialized", params)

    def notify_notebook_document_did_change(self, params: DidChangeNotebookDocumentParams) -> None:
        """Send a ``notebookDocument/didChange`` notification.


        """
        self.lsp.notify("notebookDocument/didChange", params)

    def notify_notebook_document_did_close(self, params: DidCloseNotebookDocumentParams) -> None:
        """Send a ``notebookDocument/didClose`` notification.

        A notification sent when a notebook closes.

        @since 3.17.0
        """
        self.lsp.notify("notebookDocument/didClose", params)

    def notify_notebook_document_did_open(self, params: DidOpenNotebookDocumentParams) -> None:
        """Send a ``notebookDocument/didOpen`` notification.

        A notification sent when a notebook opens.

        @since 3.17.0
        """
        self.lsp.notify("notebookDocument/didOpen", params)

    def notify_notebook_document_did_save(self, params: DidSaveNotebookDocumentParams) -> None:
        """Send a ``notebookDocument/didSave`` notification.

        A notification sent when a notebook document is saved.

        @since 3.17.0
        """
        self.lsp.notify("notebookDocument/didSave", params)

    def notify_progress(self, params: ProgressParams) -> None:
        """Send a ``$/progress`` notification.


        """
        self.lsp.notify("$/progress", params)

    def notify_set_trace(self, params: SetTraceParams) -> None:
        """Send a ``$/setTrace`` notification.


        """
        self.lsp.notify("$/setTrace", params)

    def notify_text_document_did_change(self, params: DidChangeTextDocumentParams) -> None:
        """Send a ``textDocument/didChange`` notification.

        The document change notification is sent from the client to the server
        to signal changes to a text document.
        """
        self.lsp.notify("textDocument/didChange", params)

    def notify_text_document_did_close(self, params: DidCloseTextDocumentParams) -> None:
        """Send a ``textDocument/didClose`` notification.

        The document close notification is sent from the client to the server
        when the document got closed in the client.

        The document's truth now exists where the document's uri points to
        (e.g. if the document's uri is a file uri the truth now exists on
        disk). As with the open notification the close notification is about
        managing the document's content. Receiving a close notification
        doesn't mean that the document was open in an editor before. A close
        notification requires a previous open notification to be sent.
        """
        self.lsp.notify("textDocument/didClose", params)

    def notify_text_document_did_open(self, params: DidOpenTextDocumentParams) -> None:
        """Send a ``textDocument/didOpen`` notification.

        The document open notification is sent from the client to the server to
        signal newly opened text documents.

        The document's truth is now managed by the client and the server
        must not try to read the document's truth using the document's uri.
        Open in this sense means it is managed by the client. It doesn't
        necessarily mean that its content is presented in an editor. An open
        notification must not be sent more than once without a corresponding
        close notification send before. This means open and close
        notification must be balanced and the max open count is one.
        """
        self.lsp.notify("textDocument/didOpen", params)

    def notify_text_document_did_save(self, params: DidSaveTextDocumentParams) -> None:
        """Send a ``textDocument/didSave`` notification.

        The document save notification is sent from the client to the server
        when the document got saved in the client.
        """
        self.lsp.notify("textDocument/didSave", params)

    def notify_text_document_will_save(self, params: WillSaveTextDocumentParams) -> None:
        """Send a ``textDocument/willSave`` notification.

        A document will save notification is sent from the client to the server
        before the document is actually saved.
        """
        self.lsp.notify("textDocument/willSave", params)

    def notify_window_work_done_progress_cancel(self, params: WorkDoneProgressCancelParams) -> None:
        """Send a ``window/workDoneProgress/cancel`` notification.

        The `window/workDoneProgress/cancel` notification is sent from  the
        client to the server to cancel a progress initiated on the server side.
        """
        self.lsp.notify("window/workDoneProgress/cancel", params)

    def notify_workspace_did_change_configuration(self, params: DidChangeConfigurationParams) -> None:
        """Send a ``workspace/didChangeConfiguration`` notification.

        The configuration change notification is sent from the client to the
        server when the client's configuration has changed.

        The notification contains the changed configuration as defined by
        the language client.
        """
        self.lsp.notify("workspace/didChangeConfiguration", params)

    def notify_workspace_did_change_watched_files(self, params: DidChangeWatchedFilesParams) -> None:
        """Send a ``workspace/didChangeWatchedFiles`` notification.

        The watched files notification is sent from the client to the server
        when the client detects changes to file watched by the language client.
        """
        self.lsp.notify("workspace/didChangeWatchedFiles", params)

    def notify_workspace_did_change_workspace_folders(self, params: DidChangeWorkspaceFoldersParams) -> None:
        """Send a ``workspace/didChangeWorkspaceFolders`` notification.

        The `workspace/didChangeWorkspaceFolders` notification is sent from the
        client to the server when the workspace folder configuration changes.
        """
        self.lsp.notify("workspace/didChangeWorkspaceFolders", params)

    def notify_workspace_did_create_files(self, params: CreateFilesParams) -> None:
        """Send a ``workspace/didCreateFiles`` notification.

        The did create files notification is sent from the client to the server
        when files were created from within the client.

        @since 3.16.0
        """
        self.lsp.notify("workspace/didCreateFiles", params)

    def notify_workspace_did_delete_files(self, params: DeleteFilesParams) -> None:
        """Send a ``workspace/didDeleteFiles`` notification.

        The will delete files request is sent from the client to the server
        before files are actually deleted as long as the deletion is triggered from
        within the client.

        @since 3.16.0
        """
        self.lsp.notify("workspace/didDeleteFiles", params)

    def notify_workspace_did_rename_files(self, params: RenameFilesParams) -> None:
        """Send a ``workspace/didRenameFiles`` notification.

        The did rename files notification is sent from the client to the server
        when files were renamed from within the client.

        @since 3.16.0
        """
        self.lsp.notify("workspace/didRenameFiles", params)
