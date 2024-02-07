``completion``
==============

Capabilities relating to the :lsp:`textDocument/completion` request.

.. default-domain:: capabilities

.. bool-table:: text_document.completion.dynamic_registration

.. bool-table:: text_document.completion.context_support

.. values-table:: text_document.completion.insert_text_mode

``completionItem``
------------------

.. bool-table:: text_document.completion.completion_item.snippet_support

.. bool-table:: text_document.completion.completion_item.commit_characters_support

.. values-table:: text_document.completion.completion_item.documentation_format
   :value-set: MarkupKind

.. bool-table:: text_document.completion.completion_item.deprecated_support

.. bool-table:: text_document.completion.completion_item.preselect_support

.. bool-table:: text_document.completion.completion_item.insert_replace_support

.. bool-table:: text_document.completion.completion_item.label_details_support

``insertTextModeSupport``
^^^^^^^^^^^^^^^^^^^^^^^^^

.. values-table:: text_document.completion.completion_item.insert_text_mode_support.value_set
   :value-set: InsertTextMode

``resolveSupport``
^^^^^^^^^^^^^^^^^^

.. values-table:: text_document.completion.completion_item.resolve_support.properties


``tagSupport``
^^^^^^^^^^^^^^

.. values-table:: text_document.completion.completion_item.tag_support.value_set
   :value-set: CompletionItemTag


``completionItemKind``
----------------------

.. values-table:: text_document.completion.completion_item_kind.value_set
   :value-set: CompletionItemKind

``completionList``
------------------

.. values-table:: text_document.completion.completion_list.item_defaults
