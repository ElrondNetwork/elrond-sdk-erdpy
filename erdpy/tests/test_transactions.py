import logging

from erdpy.accounts import Account
from erdpy.tests.utils import MyTestCase
from erdpy.transactions import Transaction

logging.basicConfig(level=logging.INFO)


class TransactionsTestCase(MyTestCase):
    def setUp(self):
        super().setUp()
        self.alice = Account(pem_file=str(self.devnet_wallets.joinpath("users", "alice.pem")))

    def test_serialize_transaction_payload(self):
        # With data field
        transaction = Transaction()
        transaction.nonce = 0
        transaction.value = "42"
        transaction.sender = "alice"
        transaction.receiver = "bob"
        transaction.gasPrice = 43
        transaction.gasLimit = 44
        transaction.data = "foobar"
        transaction.chainID = "BoN"
        transaction.version = 1
        serialized = transaction.serialize().decode()
        self.assertEqual("""{"nonce":0,"value":"42","receiver":"bob","sender":"alice","gasPrice":43,"gasLimit":44,"data":"Zm9vYmFy","chainID":"BoN","version":1}""", serialized)

        # Without data field
        transaction.data = ""
        serialized = transaction.serialize().decode()
        self.assertEqual("""{"nonce":0,"value":"42","receiver":"bob","sender":"alice","gasPrice":43,"gasLimit":44,"chainID":"BoN","version":1}""", serialized)

        # With actual addresses
        transaction = Transaction()
        transaction.nonce = 0
        transaction.value = "0"
        transaction.sender = "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz"
        transaction.receiver = "erd188nydpkagtpwvfklkl2tn0w6g40zdxkwfgwpjqc2a2m2n7ne9g8q2t22sr"
        transaction.gasPrice = 200000000000000
        transaction.gasLimit = 500000000
        transaction.data = "foo"
        transaction.chainID = "BoN"
        transaction.version = 1
        serialized = transaction.serialize().decode()
        self.assertEqual("""{"nonce":0,"value":"0","receiver":"erd188nydpkagtpwvfklkl2tn0w6g40zdxkwfgwpjqc2a2m2n7ne9g8q2t22sr","sender":"erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz","gasPrice":200000000000000,"gasLimit":500000000,"data":"Zm9v","chainID":"BoN","version":1}""", serialized)

    def test_serialize_transaction_with_usernames(self):
        transaction = Transaction()
        transaction.nonce = 89
        transaction.value = "0"
        transaction.sender = "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
        transaction.receiver = "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
        transaction.senderUsername = "alice"
        transaction.receiverUsername = "bob"
        transaction.gasPrice = 1000000000
        transaction.gasLimit = 50000
        transaction.data = ""
        transaction.chainID = "localnet"
        transaction.version = 1

        serialized = transaction.serialize().decode()
        self.assertEqual("""{"nonce":89,"value":"0","receiver":"erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx","sender":"erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th","senderUsername":"YWxpY2U=","receiverUsername":"Ym9i","gasPrice":1000000000,"gasLimit":50000,"chainID":"localnet","version":1}""", serialized)
        
        transaction.sign(self.alice)
        self.assertEqual("f872ea6d43b86ba6b22a7f62319a972124fc6dbd6b0743fa6465819a14d7a90100be865affb030bddf7ed86e648236cd20b1d5078e805b5419d43f3c5032b006", transaction.signature)    

    def test_serialize_transaction_as_inner(self):
        transaction = Transaction()
        transaction.nonce = 0
        transaction.value = "0"
        transaction.sender = "erd1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsmsgldz"
        transaction.receiver = "erd188nydpkagtpwvfklkl2tn0w6g40zdxkwfgwpjqc2a2m2n7ne9g8q2t22sr"
        transaction.gasPrice = 200000000000000
        transaction.gasLimit = 500000000
        transaction.data = "foo"
        transaction.chainID = "BoN"
        transaction.version = 1
        transaction.sign(self.alice)
        serialized = transaction.serialize_as_inner()

        self.assertEqual("relayedTx@7b226e6f6e6365223a302c2276616c7565223a302c227265636569766572223a224f655a47687431437775596d33376655756233615256346d6d73354b48426b4443757132716670354b67343d222c2273656e646572223a222f576b62746568644543614832424235332f7a6f517454634d6f4a323074544744592f5277304d384d704d3d222c226761735072696365223a3230303030303030303030303030302c226761734c696d6974223a3530303030303030302c2264617461223a225a6d3976222c22636861696e4944223a22516d394f222c2276657273696f6e223a312c227369676e6174757265223a224a38433741664278376f594e79746b713542564845367a4f6f7563596a796a4e79375a47484961485139674f3354384a75442f325147507650724f694f58444b5031744274643338596a667a37384f736a624a7743673d3d227d", serialized)
