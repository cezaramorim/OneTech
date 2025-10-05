from decimal import Decimal
from django.test import TestCase
from producao.utils_uom import (
    g_to_kg,
    kg_to_g,
    q3,
    calc_biomassa_kg,
    calc_racao_kg,
    calc_fcr
)

class UOMUtilsTestCase(TestCase):
    """Testes para as funções utilitárias de Unidades de Medida."""

    def test_g_to_kg(self):
        """Testa a conversão de gramas para quilogramas."""
        self.assertEqual(g_to_kg(1000), Decimal('1.000'))
        self.assertEqual(g_to_kg(500), Decimal('0.500'))
        self.assertEqual(g_to_kg(1234.56), Decimal('1.235')) # Testa arredondamento
        self.assertEqual(g_to_kg(0), Decimal('0.000'))
        self.assertEqual(g_to_kg(None), Decimal('0.000'))

    def test_kg_to_g(self):
        """Testa a conversão de quilogramas para gramas."""
        self.assertEqual(kg_to_g(1), Decimal('1000.0'))
        self.assertEqual(kg_to_g(Decimal('0.5')), Decimal('500.0'))
        self.assertEqual(kg_to_g(Decimal('1.2345')), Decimal('1234.5')) # Testa arredondamento
        self.assertEqual(kg_to_g(0), Decimal('0.0'))
        self.assertEqual(kg_to_g(None), Decimal('0'))

    def test_q3(self):
        """Testa a função de quantização para 3 casas decimais."""
        self.assertEqual(q3(1.2345), Decimal('1.235'))
        self.assertEqual(q3(1.2344), Decimal('1.234'))
        self.assertEqual(q3(100), Decimal('100.000'))
        self.assertEqual(q3(None), Decimal('0.000'))

    def test_calc_biomassa_kg(self):
        """Testa o cálculo de biomassa em kg."""
        # Caso padrão
        self.assertEqual(calc_biomassa_kg(1000, 150.5), Decimal('150.500'))
        # Com valores decimais
        self.assertEqual(calc_biomassa_kg(500, 80.75), Decimal('40.375'))
        # Com zero
        self.assertEqual(calc_biomassa_kg(0, 100), Decimal('0.000'))
        self.assertEqual(calc_biomassa_kg(1000, 0), Decimal('0.000'))
        # Com None
        self.assertEqual(calc_biomassa_kg(None, 100), Decimal('0.000'))
        self.assertEqual(calc_biomassa_kg(1000, None), Decimal('0.000'))

    def test_calc_racao_kg(self):
        """Testa o cálculo da ração sugerida em kg."""
        # Caso padrão
        self.assertEqual(calc_racao_kg(Decimal('150.500'), Decimal('5.0')), Decimal('7.525'))
        # Com percentual que exige arredondamento
        self.assertEqual(calc_racao_kg(Decimal('100.000'), Decimal('3.126')), Decimal('3.126'))
        self.assertEqual(calc_racao_kg(Decimal('100.000'), Decimal('3.1267')), Decimal('3.127'))
        # Com zero
        self.assertEqual(calc_racao_kg(0, 5), Decimal('0.000'))
        self.assertEqual(calc_racao_kg(150, 0), Decimal('0.000'))
        # Com None
        self.assertEqual(calc_racao_kg(None, 5), Decimal('0.000'))
        self.assertEqual(calc_racao_kg(150, None), Decimal('0.000'))

    def test_calc_fcr(self):
        """Testa o cálculo do Fator de Conversão Alimentar (FCR)."""
        # Caso ideal
        self.assertEqual(calc_fcr(Decimal('120.0'), Decimal('100.0')), Decimal('1.20'))
        # Com arredondamento
        self.assertEqual(calc_fcr(Decimal('120.0'), Decimal('99.9')), Decimal('1.20'))
        self.assertEqual(calc_fcr(Decimal('120.555'), Decimal('100.123')), Decimal('1.20'))
        # Divisão por zero
        self.assertEqual(calc_fcr(Decimal('120.0'), Decimal('0')), Decimal('0.00'))
        self.assertEqual(calc_fcr(Decimal('120.0'), 0), Decimal('0.00'))
        # Com None
        self.assertEqual(calc_fcr(None, 100), Decimal('0.00'))
        self.assertEqual(calc_fcr(120, None), Decimal('0.00'))
