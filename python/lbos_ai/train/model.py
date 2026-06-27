"""
Transformer language model implementation for LBOS-AI
Based on transformer architecture but simplified for efficiency
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict

class MultiHeadSelfAttention(nn.Module):
    def __init__(self, hidden_size: int, num_attention_heads: int, dropout_prob: float = 0.1):
        super().__init__()
        if hidden_size % num_attention_heads != 0:
            raise ValueError(
                f"Hidden size {hidden_size} must be divisible by number of attention heads {num_attention_heads}"
            )

        self.num_attention_heads = num_attention_heads
        self.attention_head_size = int(hidden_size / num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.query = nn.Linear(hidden_size, self.all_head_size)
        self.key = nn.Linear(hidden_size, self.all_head_size)
        self.value = nn.Linear(hidden_size, self.all_head_size)

        self.dropout = nn.Dropout(dropout_prob)
        self.output_dense = nn.Linear(hidden_size, hidden_size)
        self.output_dropout = nn.Dropout(dropout_prob)
        self.output_layernorm = nn.LayerNorm(hidden_size, eps=1e-12)

    def transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        head_mask: Optional[torch.Tensor] = None,
        encoder_hidden_states: Optional[torch.Tensor] = None,
        encoder_attention_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor]:
        mixed_query_layer = self.query(hidden_states)
        mixed_key_layer = self.key(hidden_states)
        mixed_value_layer = self.value(hidden_states)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        # Apply the attention mask is (precomputed for all layers in BertModel forward() function)
        if attention_mask is not None:
            # Apply the attention mask
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities.
        attention_probs = nn.Softmax(dim=-1)(attention_scores)

        # This is actually dropping out entire tokens to attend to, which might
        # seem strange, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        # Mask heads if we want to
        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        output = self.output_dense(context_layer)
        output = self.output_dropout(output)
        output = self.output_layernorm(output + hidden_states)

        outputs = (output, attention_probs) if output_attentions else (output,)
        return outputs


class FeedForwardNetwork(nn.Module):
    def __init__(self, hidden_size: int, intermediate_size: int, hidden_act: str, dropout_prob: float = 0.1):
        super().__init__()
        self.dense1 = nn.Linear(hidden_size, intermediate_size)
        self.intermediate_act_fn = self._get_activation_fn(hidden_act)
        self.dense2 = nn.Linear(intermediate_size, hidden_size)
        self.dropout = nn.Dropout(dropout_prob)
        self.layernorm = nn.LayerNorm(hidden_size, eps=1e-12)

    def _get_activation_fn(self, activation: str):
        if activation == "gelu":
            return F.gelu
        elif activation == "relu":
            return F.relu
        elif activation == "swish":
            return F.silu
        else:
            raise ValueError(f"Unsupported activation function: {activation}")

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.dense1(hidden_states)
        hidden_states = self.intermediate_act_fn(hidden_states)
        hidden_states = self.dense2(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.layernorm(hidden_states + hidden_states)
        return hidden_states


class TransformerLayer(nn.Module):
    def __init__(self, hidden_size: int, num_attention_heads: int, intermediate_size: int,
                 hidden_act: str, hidden_dropout_prob: float = 0.1,
                 attention_probs_dropout_prob: float = 0.1):
        super().__init__()
        self.attention = MultiHeadSelfAttention(
            hidden_size, num_attention_heads, attention_probs_dropout_prob
        )
        self.intermediate = FeedForwardNetwork(
            hidden_size, intermediate_size, hidden_act, hidden_dropout_prob
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        head_mask: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor]:
        self_attention_outputs = self.attention(
            hidden_states,
            attention_mask,
            head_mask,
            output_attentions=output_attentions,
        )
        attention_output = self_attention_outputs[0]
        outputs = self_attention_outputs[1:]  # add attention outputs if we output them

        intermediate_output = self.intermediate(attention_output)
        layer_output = intermediate_output
        outputs = (layer_output,) + outputs
        return outputs


class TransformerLM(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        hidden_size: int = 768,
        num_hidden_layers: int = 6,
        num_attention_heads: int = 12,
        intermediate_size: int = 3072,
        hidden_act: str = "gelu",
        hidden_dropout_prob: float = 0.1,
        attention_probs_dropout_prob: float = 0.1,
        max_position_embeddings: int = 512,
        type_vocab_size: int = 2,
        initializer_range: float = 0.02,
        pad_token_id: int = 0,
    ):
        super().__init__()
        self.pad_token_id = pad_token_id
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.hidden_act = hidden_act

        self.embeddings = Embeddings(
            vocab_size=vocab_size,
            hidden_size=hidden_size,
            max_position_embeddings=max_position_embeddings,
            type_vocab_size=type_vocab_size,
            pad_token_id=pad_token_id
        )

        self.encoder = nn.ModuleList([
            TransformerLayer(
                hidden_size=hidden_size,
                num_attention_heads=num_attention_heads,
                intermediate_size=intermediate_size,
                hidden_act=hidden_act,
                hidden_dropout_prob=hidden_dropout_prob,
                attention_probs_dropout_prob=attention_probs_dropout_prob
            )
            for _ in range(num_hidden_layers)
        ])

        self.pooler = nn.Linear(hidden_size, hidden_size)
        self.pooler_activation = nn.Tanh()

        # Language modeling head
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)

        # Initialize weights
        self.apply(self._init_weights)

        # Tie weights between embeddings and lm_head if desired
        # self.lm_head.weight = self.embeddings.word_embeddings.weight

    def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.Linear):
            # Slightly different from the TF version which uses truncated_normal for initialization
            # cf https://github.com/pytorch/pytorch/pull/5617
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        elif isinstance(module, nn.LayerNorm):
            module.weight.data.fill_(1.0)
            module.bias.data.zero_()

    def get_input_embeddings(self):
        return self.embeddings.word_embeddings

    def set_input_embeddings(self, value):
        self.embeddings.word_embeddings = value

    def _prune_heads(self, heads_to_prune):
        """
        Prunes heads of the model.
        heads_to_prune: dict of {layer_num: list of heads to prune in this layer}
        See base class PreTrainedModel
        """
        for layer, heads in heads_to_prune.items():
            self.encoder[layer].attention.prune_heads(heads)

    def forward(
        self,
        input_ids: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None,
        head_mask: Optional[torch.Tensor] = None,
        inputs_embeds: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = True,
    ) -> dict:
        """
        Forward pass of the model

        Args:
            input_ids: Indices of input sequence tokens in the vocabulary
            attention_mask: Mask to avoid performing attention on padding token indices
            token_type_ids: Segment token indices to indicate first and second portions of the inputs
            position_ids: Indices of positions of each input sequence tokens in the position embeddings
            head_mask: Mask to nullify selected heads of the self-attention modules
            inputs_embeds: Optionally, instead of passing input_ids you can choose to directly pass an embedded representation
            labels: Labels for language modeling (note: labels will be shifted to the left)
            output_attentions: Whether to return attentions tensors
            output_hidden_states: Whether to return hidden states of all layers
            return_dict: Whether to return a dict or tuple

        Returns:
            Dictionary containing loss, logits, hidden_states, attentions
        """
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            input_shape = input_ids.size()
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        batch_size, seq_length = input_shape
        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if attention_mask is None:
            attention_mask = torch.ones(((batch_size, seq_length)), device=device)
        if token_type_ids is None:
            token_type_ids = torch.zeros((batch_size, seq_length), dtype=torch.long, device=device)

        # We can provide a self-attention mask of dimensions [batch_size, from_to, from_to, to_to]
        # ourselves in which case we just need to make it broadcastable to all heads.
        extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(attention_mask, input_shape, device)

        # Prepare head mask if needed
        # 1.0 in head_mask indicate we keep the head
        # attention_probs has shape bsz x n_heads x N x N
        # input head_mask has shape [num_heads] or [num_hidden_layers x num_heads]
        # NOTE: head_mask is specific to each layer, so we need to specify per layer
        if head_mask is not None:
            if head_mask.dim() == 1:
                head_mask = (
                    head_mask.unsqueeze(0)
                    .unsqueeze(0)
                    .unsqueeze(-1)
                    .unsqueeze(-1)
                    .expand((self.num_hidden_layers, -1, -1, -1, -1))
                )
            elif head_mask.dim() == 2:
                # We need to provide 1 for head, 1 for batch, and 1 for sequence (feature dimension)
                # to get the correct shape for broadcasting to all heads
                # but the actual shape for the head_mask choice is (num_hidden_layers, batch, seq_length, 1, 1)
                head_mask = (
                    head_mask.unsqueeze(1)
                    .unsqueeze(1)
                    .unsqueeze(-1)
                    .unsqueeze(-1)
                    .expand((self.num_hidden_layers, -1, -1, -1, -1))
                )
        else:
            head_mask = [None] * self.num_hidden_layers

        embedding_output = self.embeddings(
            input_ids=input_ids,
            position_ids=position_ids,
            token_type_ids=token_type_ids
        )
        encoder_outputs = self.encoder(
            embedding_output,
            attention_mask=extended_attention_mask,
            head_mask=head_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = encoder_outputs[0]

        # Prediction scores (language modeling head)
        prediction_scores = self.lm_head(sequence_output)

        total_loss = None
        if labels is not None:
            # Shift so that tokens < n predict n
            shift_logits = prediction_scores[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()
            # Flatten the tokens
            loss_fct = nn.CrossEntropyLoss(ignore_index=-1)
            loss = loss_fct(shift_logits.view(-1, self.vocab_size), shift_labels.view(-1))
            total_loss = loss

        if not return_dict:
            output = (prediction_scores,) + encoder_outputs[1:]
            return ((total_loss,) + output) if total_loss is not None else output

        return {
            "loss": total_loss,
            "logits": prediction_scores,
            "hidden_states": encoder_outputs[2] if output_hidden_states else None,
            "attentions": encoder_outputs[3] if output_attentions else None,
        }

    def get_extended_attention_mask(self, attention_mask: torch.Tensor, input_shape: Tuple[int, int], device: torch.device) -> torch.Tensor:
        """
        Makes broadcastable attention and causal masks so that future and masked token positions are ignored.

        Args:
            attention_mask: Tensor with shape [batch_size, seq_length]
            input_shape: Tuple of (batch_size, seq_length)
            device: Target device for tensors

        Returns:
            Tensor with shape [batch_size, 1, 1, seq_length] or [batch_size, 1, seq_length, seq_length]
        """
        # We can provide a self-attention mask of dimensions [batch_size, from_to, from_state, to_state]
        # ourselves in which case we just need to make it broadcastable to all heads.
        if attention_mask.dim() == 3:
            extended_attention_mask = attention_mask[:, None, :, :]
        elif attention_mask.dim() == 2:
            # Provided a padding mask of dimensions [batch_size, seq_length]
            # If the model is a decoder, apply a causal mask in addition to the padding mask
            # If the model is an encoder, make the mask broadcastable to [batch_size, num_heads, seq_length, seq_length]
            extended_attention_mask = attention_mask[:, None, None, :]
        else:
            raise ValueError(
                f"Wrong shape for attention_mask (shape {attention_mask.shape})"
            )

        # Since attention_mask is 1.0 for positions we want to attend and 0.0 for
        # masked positions, this operation will create a tensor which is 0.0 for
        # positions we want to attend and -10000.0 for positions we want to mask.
        extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0

        return extended_attention_mask


class Embeddings(nn.Module):
    """Construct the embeddings from word, position and token_type embeddings."""

    def __init__(self, vocab_size: int, hidden_size: int, max_position_embeddings: int,
                 type_vocab_size: int, pad_token_id: int = 0):
        super().__init__()
        self.word_embeddings = nn.Embedding(vocab_size, hidden_size, padding_idx=pad_token_id)
        self.position_embeddings = nn.Embedding(max_position_embeddings, hidden_size)
        self.token_type_embeddings = nn.Embedding(type_vocab_size, hidden_size)

        # Self-LayerNorm is not snake-cased to stick with TensorFlow model variable name and be able to load
        # any TensorFlow checkpoint file
        self.LayerNorm = nn.LayerNorm(hidden_size, eps=1e-12)
        self.dropout = nn.Dropout(0.1)
        self.position_ids = torch.arange(max_position_embeddings).expand((1, -1))
        self.position_embedding_type = "absolute"

    def forward(
        self, input_ids: Optional[torch.Tensor] = None, token_type_ids: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None, inputs_embeds: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        if input_ids is not None:
            input_shape = input_ids.size()
        else:
            input_shape = inputs_embeds.size()[:-1]

        seq_length = input_shape[1]

        if position_ids is None:
            position_ids = self.position_ids[:, :seq_length]

        # Setting the token_type_ids to the registered buffer in constructor where it is all zeros, which means it
        # doesn't affect loss when audio upstream, because it doesn't add any information to the token.
        if token_type_ids is None:
            if hasattr(self, "token_type_ids"):
                buffered_token_type_ids = self.token_type_ids[:, :seq_length]
                buffered_token_type_ids = buffered_token_type_ids.expand((input_shape[0], -1))
                if buffer_tensors:
                    token_type_ids = buffered_token_type_ids
            else:
                token_type_ids = torch.zeros((input_shape[0], seq_length), dtype=torch.long, device=self.position_ids.device)

        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)
        position_embeddings = self.position_embeddings(position_ids)
        token_type_embeddings = self.token_type_embeddings(token_type_ids)

        embeddings = inputs_embeds + position_embeddings + token_type_embeddings
        embeddings = self.LayerNorm(embeddings)
        embeddings = self.dropout(embeddings)
        return embeddings
