"""Tests for sterilization awareness campaign page (RAP-629)."""

from __future__ import annotations

from pathlib import Path


class TestPageStructure:
    """Verify page file exists and has correct structure."""

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/educacion/esterilizacion/page.tsx").exists()

    def test_is_client_component(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert '"use client"' in content

    def test_exports_default_page(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "export default function SterilizationAwarenessPage" in content


class TestHeroSection:
    """Test hero section content."""

    def test_has_hero_title(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Esterilizacion: Un Acto de Amor" in content

    def test_has_hero_subtitle(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "decision" in content.lower()

    def test_has_cta_button(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Agendar esterilizacion" in content

    def test_has_whatsapp_link(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "wa.me" in content


class TestBenefitsSection:
    """Test benefits section."""

    def test_has_benefits_heading(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Beneficios de la esterilizacion" in content

    def test_has_benefit_cards(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "BenefitCard" in content

    def test_has_six_benefits(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Mejor salud" in content
        assert "Menos abandonos" in content
        assert "Comunidades mas seguras" in content
        assert "Mejor comportamiento" in content
        assert "Ahorro economico" in content
        assert "Impacto ambiental" in content

    def test_has_benefit_descriptions(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "cancer" in content.lower()
        assert "sobrepoblacion" in content


class TestMythsSection:
    """Test myths vs reality section."""

    def test_has_myths_heading(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Mitos y Realidades" in content

    def test_has_myth_cards(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "MythCard" in content

    def test_has_five_myths(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "camada" in content
        assert "personalidad" in content
        assert "cara" in content.lower()
        assert "engordar" in content

    def test_myth_has_reality_response(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Realidad:" in content
        assert "Mito:" in content


class TestFAQSection:
    """Test FAQ section."""

    def test_has_faq_heading(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Preguntas frecuentes" in content

    def test_has_faq_items(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "FAQItem" in content

    def test_faq_is_expandable(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "isOpen" in content
        assert "setIsOpen" in content

    def test_has_four_faqs(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "edad" in content
        assert "recuperacion" in content
        assert "Paraguay" in content
        assert "dolorosa" in content


class TestStatistics:
    """Test statistics section."""

    def test_has_stat_cards(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "StatCard" in content

    def test_has_percentage_stats(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "70%" in content
        assert "200%" in content
        assert "80%" in content

    def test_has_responsive_grid(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "grid-cols-2" in content
        assert "sm:grid-cols-4" in content


class TestCTASection:
    """Test call-to-action section."""

    def test_has_cta_heading(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "Sumate a la causa" in content

    def test_has_whatsapp_button(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "WhatsApp" in content

    def test_has_contact_button(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "/contacto" in content


class TestAccessibility:
    """Test accessibility features."""

    def test_aria_labels(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "aria-label" in content

    def test_section_landmarks(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert 'aria-label="Estadisticas' in content
        assert 'aria-label="Beneficios' in content
        assert 'aria-label="Mitos' in content
        assert 'aria-label="Preguntas' in content

    def test_faq_aria_expanded(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "aria-expanded" in content

    def test_touch_targets(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "min-h-[44px]" in content

    def test_role_group_for_stats(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert 'role="group"' in content

    def test_role_list_for_faq(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert 'role="list"' in content
        assert 'role="listitem"' in content


class TestResponsive:
    """Test responsive design."""

    def test_responsive_grid_benefits(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "sm:grid-cols-2" in content
        assert "lg:grid-cols-3" in content

    def test_responsive_buttons(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "sm:flex-row" in content

    def test_responsive_hero_text(self) -> None:
        content = Path("frontend/src/app/educacion/esterilizacion/page.tsx").read_text()
        assert "sm:text-4xl" in content
