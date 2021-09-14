from inspect import trace
from django.test import TestCase

from .models import Block, Transaction

class TestViewAddTransaction(TestCase):
    def setUp(self) -> None:
        pass

    def test_add_transaction_true_1(self):
        data = {
            "sender":"0123456789012345678901234567890123",
            "receiver":"0123456789012345678901234567890124",
            "value":10,
            "timestamp":"2000-01-01T20:20"
        }
        res = self.client.post('/chain/add_transaction/', data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_json['OK'])
    
    def test_required_field_false_1(self):
        data = {
        }
        res = self.client.post('/chain/add_transaction/', data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res_json['OK'])
        self.assertEqual(res_json['message']['sender'][0],    'This field is required.')
        self.assertEqual(res_json['message']['receiver'][0],  'This field is required.')
        self.assertEqual(res_json['message']['value'][0],     'This field is required.')
        self.assertEqual(res_json['message']['timestamp'][0], 'This field is required.')

    def test_validate_receiver_sender_false_2(self):
        data = {
            "sender":"012345678901234567890123456789012",
            "receiver":"012345678901234567890123456789012",
            "value":10,
            "timestamp":"2000-01-01T20:20"
        }
        res = self.client.post('/chain/add_transaction/', data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res_json['OK'])
        self.assertEqual(res_json['message']['sender'][0],    'sender address is invalid.')
        self.assertEqual(res_json['message']['receiver'][0],  'receiver address is invalid.')

class TestViewAddBlock(TestCase):
    def setUp(self) -> None:
        Transaction.objects.create(
            sender="0123456789012345678901234567890123",
            receiver="0123456789012345678901234567890124",
            value=10,
            timestamp="2000-01-01T20:20"
        )
        Transaction.objects.create(
            sender="0123456789012345678901234567890123",
            receiver="0123456789012345678901234567890124",
            value=10,
            timestamp="2000-01-01T20:20"
        )
        Transaction.objects.create(
            sender="0123456789012345678901234567890123",
            receiver="0123456789012345678901234567890124",
            value=10,
            timestamp="2000-01-01T20:20"
        )
        Transaction.objects.create(
            sender="0123456789012345678901234567890123",
            receiver="0123456789012345678901234567890124",
            value=10,
            timestamp="2000-01-01T20:20"
        )

    def true_init_add_block(self):
        data = {
            "hash_block":"0123456789012345678901234567890123",
            "prev_block":"",
            "transactions":[1,2,3],
            "timestamp":"2000-01-01T20:20",
            "difficulty":10,
            "nonce":1
        }
        res = self.client.post("/chain/add_block/", data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_json['OK'])
        blocks = Block.objects.all()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(blocks[0].transactions.all()), 3)

    def true_second_add_block(self):
        data = {
            "hash_block":"0123456789012345678901234567890124",
            "prev_block":"1",
            "transactions":[4],
            "timestamp":"2000-01-01T20:30",
            "difficulty":10,
            "nonce":10
        }
        res = self.client.post("/chain/add_block/", data=data)
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertTrue(res_json['OK'])
        block:Block = Block.objects.get(id=2)
        self.assertIsNotNone(block)
        self.assertEqual(len(block.transactions.all()), 1)

    def false_init_add_block(self):
        pass

    def false_second_transaction_add_block(self):
        pass

    def test_init_block_true_1(self):
        self.true_init_add_block()
        self.true_second_add_block
        
    def test_init_block_false_1(self):
        data = {
            "hash_block":"0123456789012345678901234567890123",
            "prev_block":"1",
            "transactions":[1,2,3],
            "timestamp":"2000-01-01T20:20",
            "difficulty":10,
            "nonce":1
        }
        res = self.client.post("/chain/add_block/", data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res_json['OK'])
        blocks = Block.objects.all()
        self.assertEqual(len(blocks), 0)

    def test_second_block_false_1(self):
        self.true_init_add_block()
        data = {
            "hash_block":"0123456789012345678901234567890124",
            "prev_block":"1",
            "transactions":[1],
            "timestamp":"2000-01-01T20:30",
            "difficulty":10,
            "nonce":10
        }
        res = self.client.post("/chain/add_block/", data=data)
        res_json = res.json()
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res_json['OK'])
        block:Block = Block.objects.filter(id=2).first()
        self.assertIsNone(block)
    

