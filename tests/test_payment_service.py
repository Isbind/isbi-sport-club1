import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

from payment_service import PaymentService
from config import PATHS


def setup_qrcode_dir(tmp_path, monkeypatch):
    temp_qr = tmp_path / "qrcodes"
    temp_qr.mkdir()
    monkeypatch.setitem(PATHS, 'qrcodes', str(temp_qr))
    return str(temp_qr)


def test_generate_payment_reference():
    ref = PaymentService.generate_payment_reference('TST')
    assert isinstance(ref, str)
    assert ref.startswith('TST-')


def test_process_cash_payment():
    res = PaymentService.process_cash_payment(1500, 'Test paiement espèces')
    assert res['success'] is True
    assert res['method'] == 'cash'
    assert 'reference' in res


@patch('payment_service.requests.post')
def test_process_wave_payment_mock(mock_post, tmp_path, monkeypatch):
    # Préparer le mock de réponse
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {'checkout_url': 'https://checkout.test'}
    mock_post.return_value = mock_resp

    setup_qrcode_dir(tmp_path, monkeypatch)

    res = PaymentService.process_wave_payment(2000, '221700000000', 'Test Wave')
    assert res['success'] is True
    assert res['method'] == 'wave'
    assert 'payment_url' in res
    assert res['payment_url'] == 'https://checkout.test'


@patch('payment_service.requests.post')
def test_process_orange_money_payment_mock(mock_post, tmp_path, monkeypatch):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {'payment_url': 'https://orange.test'}
    mock_post.return_value = mock_resp

    setup_qrcode_dir(tmp_path, monkeypatch)

    res = PaymentService.process_orange_money_payment(1200, '221700000001', 'Test OM')
    assert res['success'] is True
    assert res['method'] == 'orange_money'
    assert 'payment_url' in res
    assert res['payment_url'] == 'https://orange.test'
