"""Unit tests for schema module."""

from orcx.schema import QUANT_BY_BITS, ProviderPrefs


class TestProviderPrefsResolveQuantizations:
    """Tests for ProviderPrefs.resolve_quantizations()."""

    def test_explicit_quantizations_returned_directly(self) -> None:
        """When quantizations is set explicitly, return it as-is."""
        prefs = ProviderPrefs(quantizations=["fp16", "bf16"])
        result = prefs.resolve_quantizations()
        assert result == ["fp16", "bf16"]

    def test_min_bits_filters_correctly(self) -> None:
        """min_bits should include only quants at or above that bit level."""
        prefs = ProviderPrefs(min_bits=8)
        result = prefs.resolve_quantizations()

        assert result is not None
        result_set = set(result)

        # Should include 8-bit and above
        assert "int8" in result_set
        assert "fp8" in result_set
        assert "fp16" in result_set
        assert "bf16" in result_set
        assert "fp32" in result_set

        # Should NOT include below 8-bit
        assert "int4" not in result_set
        assert "fp4" not in result_set
        assert "fp6" not in result_set

    def test_min_bits_16(self) -> None:
        """min_bits=16 should include fp16, bf16, fp32."""
        prefs = ProviderPrefs(min_bits=16)
        result = prefs.resolve_quantizations()

        assert result is not None
        result_set = set(result)

        assert "fp16" in result_set
        assert "bf16" in result_set
        assert "fp32" in result_set

        assert "int8" not in result_set
        assert "fp8" not in result_set

    def test_exclude_quants_from_all(self) -> None:
        """exclude_quants alone should exclude from all possible quants."""
        prefs = ProviderPrefs(exclude_quants=["fp4", "int4"])
        result = prefs.resolve_quantizations()

        assert result is not None
        result_set = set(result)

        # All quants except excluded
        all_quants = {q for quants in QUANT_BY_BITS.values() for q in quants}
        expected = all_quants - {"fp4", "int4"}
        assert result_set == expected

    def test_min_bits_with_exclude_quants(self) -> None:
        """min_bits combined with exclude_quants should filter both."""
        prefs = ProviderPrefs(min_bits=8, exclude_quants=["fp32"])
        result = prefs.resolve_quantizations()

        assert result is not None
        result_set = set(result)

        # 8-bit and above, minus fp32
        assert "int8" in result_set
        assert "fp8" in result_set
        assert "fp16" in result_set
        assert "bf16" in result_set
        assert "fp32" not in result_set

        # Below 8-bit should still be excluded
        assert "int4" not in result_set
        assert "fp4" not in result_set

    def test_no_quantization_options_returns_none(self) -> None:
        """No quantization options set should return None."""
        prefs = ProviderPrefs()
        result = prefs.resolve_quantizations()
        assert result is None

    def test_explicit_quantizations_takes_precedence(self) -> None:
        """explicit quantizations should override min_bits and exclude."""
        prefs = ProviderPrefs(
            quantizations=["fp16"],
            min_bits=8,
            exclude_quants=["fp16"],
        )
        result = prefs.resolve_quantizations()
        # quantizations takes precedence
        assert result == ["fp16"]

    def test_min_bits_4_includes_all(self) -> None:
        """min_bits=4 should include all quantizations."""
        prefs = ProviderPrefs(min_bits=4)
        result = prefs.resolve_quantizations()

        assert result is not None
        all_quants = {q for quants in QUANT_BY_BITS.values() for q in quants}
        assert set(result) == all_quants

    def test_exclude_all_from_min_bits_returns_empty(self) -> None:
        """Excluding all quants from min_bits range returns empty list."""
        prefs = ProviderPrefs(min_bits=32, exclude_quants=["fp32"])
        result = prefs.resolve_quantizations()
        # After filtering, nothing left
        assert result == [] or result is None


class TestProviderPrefsMergeWith:
    """Tests for ProviderPrefs.merge_with()."""

    def test_merge_with_none_returns_self(self) -> None:
        """Merging with None should return self unchanged."""
        prefs = ProviderPrefs(min_bits=8, ignore=["DeepInfra"])
        result = prefs.merge_with(None)
        assert result.min_bits == 8
        assert result.ignore == ["DeepInfra"]

    def test_self_overrides_other_for_scalar_fields(self) -> None:
        """Self values should override other for scalar fields."""
        agent = ProviderPrefs(min_bits=16, sort="latency")
        global_ = ProviderPrefs(min_bits=8, sort="price")
        result = agent.merge_with(global_)
        # Agent's min_bits is higher (more restrictive), so it wins
        assert result.min_bits == 16
        # Agent's sort overrides global
        assert result.sort == "latency"

    def test_min_bits_takes_higher_value(self) -> None:
        """min_bits should take the higher (more restrictive) value."""
        agent = ProviderPrefs(min_bits=8)
        global_ = ProviderPrefs(min_bits=16)
        result = agent.merge_with(global_)
        # Global is more restrictive
        assert result.min_bits == 16

    def test_ignore_lists_are_unioned(self) -> None:
        """ignore lists should be merged (union)."""
        agent = ProviderPrefs(ignore=["DeepInfra", "Chutes"])
        global_ = ProviderPrefs(ignore=["SiliconFlow", "DeepInfra"])
        result = agent.merge_with(global_)
        # Union, preserving order (agent first)
        assert result.ignore == ["DeepInfra", "Chutes", "SiliconFlow"]

    def test_exclude_quants_are_unioned(self) -> None:
        """exclude_quants lists should be merged (union)."""
        agent = ProviderPrefs(exclude_quants=["fp4"])
        global_ = ProviderPrefs(exclude_quants=["int4", "fp4"])
        result = agent.merge_with(global_)
        assert result.exclude_quants == ["fp4", "int4"]

    def test_prefer_lists_preserve_order(self) -> None:
        """prefer lists should merge with agent first."""
        agent = ProviderPrefs(prefer=["AtlasCloud"])
        global_ = ProviderPrefs(prefer=["NovitaAI", "Phala"])
        result = agent.merge_with(global_)
        # Agent providers come first
        assert result.prefer == ["AtlasCloud", "NovitaAI", "Phala"]

    def test_only_is_overridden_not_merged(self) -> None:
        """only should be overridden by agent, not merged."""
        agent = ProviderPrefs(only=["Together"])
        global_ = ProviderPrefs(only=["Azure", "AWS"])
        result = agent.merge_with(global_)
        # Agent overrides completely
        assert result.only == ["Together"]

    def test_only_falls_back_to_global(self) -> None:
        """only should fall back to global if agent doesn't set it."""
        agent = ProviderPrefs(min_bits=8)
        global_ = ProviderPrefs(only=["Azure", "AWS"])
        result = agent.merge_with(global_)
        assert result.only == ["Azure", "AWS"]

    def test_order_is_overridden_not_merged(self) -> None:
        """order should be overridden by agent, not merged."""
        agent = ProviderPrefs(order=["A", "B"])
        global_ = ProviderPrefs(order=["C", "D"])
        result = agent.merge_with(global_)
        assert result.order == ["A", "B"]

    def test_quantizations_is_overridden_not_merged(self) -> None:
        """quantizations should be overridden by agent, not merged."""
        agent = ProviderPrefs(quantizations=["fp16"])
        global_ = ProviderPrefs(quantizations=["fp8", "fp16", "bf16"])
        result = agent.merge_with(global_)
        assert result.quantizations == ["fp16"]

    def test_allow_fallbacks_agent_false_overrides(self) -> None:
        """allow_fallbacks=False should override global True."""
        agent = ProviderPrefs(allow_fallbacks=False)
        global_ = ProviderPrefs(allow_fallbacks=True)
        result = agent.merge_with(global_)
        assert result.allow_fallbacks is False

    def test_full_merge_scenario(self) -> None:
        """Test realistic merge of agent and global prefs."""
        agent = ProviderPrefs(
            ignore=["Chutes"],
            prefer=["AtlasCloud"],
        )
        global_ = ProviderPrefs(
            min_bits=8,
            ignore=["SiliconFlow", "DeepInfra", "Mancer"],
            sort="price",
        )
        result = agent.merge_with(global_)

        assert result.min_bits == 8  # From global
        assert result.sort == "price"  # From global
        assert result.prefer == ["AtlasCloud"]  # From agent
        # ignore is unioned
        assert set(result.ignore or []) == {"Chutes", "SiliconFlow", "DeepInfra", "Mancer"}
