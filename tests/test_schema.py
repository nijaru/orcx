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
