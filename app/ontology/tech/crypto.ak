# Akasha ontology — namespace: crypto
# atoms: 32

def "crypto.analysis" "Cryptanalysis, attacks, and security evaluation."
ln crypto.analysis ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.analysis"

def "crypto.data_encryption" "Data encryption including FDE, envelope encryption, and tokenization."
ln crypto.data_encryption ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.data_encryption"

def "crypto.key_management" "Key lifecycle, KMS, HSM, and key distribution."
ln crypto.key_management ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.key_management"

def "crypto.pki" "Public Key Infrastructure including certificates, CA, and OCSP."
ln crypto.pki ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.pki"

def "crypto.post_quantum" "Post-quantum cryptography including lattice-based and hash-based schemes."
ln crypto.post_quantum ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.post_quantum"

def "crypto.primitives" "Cryptographic primitives including symmetric, asymmetric, hashing, and MAC."
ln crypto.primitives ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.primitives"

def "crypto.protocols" "Cryptographic protocols including TLS, IPsec, SSH, and QUIC."
ln crypto.protocols ont.cryptography sys:part_of
set.add name="ontology.cryptography" id="crypto.protocols"

def "crypto:aes" "AES symmetric block cipher."
ln crypto:aes crypto.primitives sys:is_a
set.add name="ontology.cryptography" id="crypto:aes"

def "crypto:brute_force" "Brute-force cryptanalysis."
ln crypto:brute_force crypto.analysis sys:is_a
set.add name="ontology.cryptography" id="crypto:brute_force"

def "crypto:ca" "Certificate Authority."
ln crypto:ca crypto.pki sys:is_a
set.add name="ontology.cryptography" id="crypto:ca"

def "crypto:chacha20" "ChaCha20 stream cipher."
ln crypto:chacha20 crypto.primitives sys:is_a
set.add name="ontology.cryptography" id="crypto:chacha20"

def "crypto:csr" "Certificate Signing Request."
ln crypto:csr crypto.pki sys:is_a
set.add name="ontology.cryptography" id="crypto:csr"

def "crypto:dilithium" "CRYSTALS-Dilithium post-quantum signature."
ln crypto:dilithium crypto.post_quantum sys:is_a
set.add name="ontology.cryptography" id="crypto:dilithium"

def "crypto:ecc" "Elliptic Curve Cryptography."
ln crypto:ecc crypto.primitives sys:is_a
ln crypto:ecc crypto:rsa @contrasts_with
set.add name="ontology.cryptography" id="crypto:ecc"

def "crypto:envelope" "Envelope encryption using data keys and master keys."
ln crypto:envelope crypto.data_encryption sys:is_a
ln crypto:envelope crypto:kms @uses
set.add name="ontology.cryptography" id="crypto:envelope"

def "crypto:fde" "Full Disk Encryption."
ln crypto:fde crypto.data_encryption sys:is_a
set.add name="ontology.cryptography" id="crypto:fde"

def "crypto:hmac" "Hash-based Message Authentication Code."
ln crypto:hmac crypto.primitives sys:is_a
set.add name="ontology.cryptography" id="crypto:hmac"

def "crypto:hsm" "Hardware Security Module."
ln crypto:hsm crypto.key_management sys:is_a
set.add name="ontology.cryptography" id="crypto:hsm"

def "crypto:ipsec" "IPsec VPN encryption protocol."
ln crypto:ipsec crypto.protocols sys:is_a
set.add name="ontology.cryptography" id="crypto:ipsec"

def "crypto:key_lifecycle" "Key generation, rotation, storage, and destruction."
ln crypto:key_lifecycle crypto.key_management sys:is_a
set.add name="ontology.cryptography" id="crypto:key_lifecycle"

def "crypto:kms" "Key Management Service."
ln crypto:kms crypto.key_management sys:is_a
set.add name="ontology.cryptography" id="crypto:kms"

def "crypto:kyber" "CRYSTALS-Kyber post-quantum KEM."
ln crypto:kyber crypto.post_quantum sys:is_a
ln crypto:kyber crypto:tls @future_supports
set.add name="ontology.cryptography" id="crypto:kyber"

def "crypto:mathematical_attack" "Mathematical cryptanalysis."
ln crypto:mathematical_attack crypto.analysis sys:is_a
set.add name="ontology.cryptography" id="crypto:mathematical_attack"

def "crypto:ocsp" "Online Certificate Status Protocol."
ln crypto:ocsp crypto.pki sys:is_a
set.add name="ontology.cryptography" id="crypto:ocsp"

def "crypto:quic_crypto" "QUIC cryptographic handshake and encryption."
ln crypto:quic_crypto crypto.protocols sys:is_a
set.add name="ontology.cryptography" id="crypto:quic_crypto"

def "crypto:rsa" "RSA public-key cryptosystem."
ln crypto:rsa crypto.primitives sys:is_a
set.add name="ontology.cryptography" id="crypto:rsa"

def "crypto:sha2" "SHA-2 cryptographic hash family."
ln crypto:sha2 crypto.primitives sys:is_a
set.add name="ontology.cryptography" id="crypto:sha2"

def "crypto:side_channel" "Side-channel attacks."
ln crypto:side_channel crypto.analysis sys:is_a
ln crypto:side_channel crypto:hsm @mitigated_by
set.add name="ontology.cryptography" id="crypto:side_channel"

def "crypto:sphincs" "SPHINCS+ hash-based signature."
ln crypto:sphincs crypto.post_quantum sys:is_a
set.add name="ontology.cryptography" id="crypto:sphincs"

def "crypto:ssh" "Secure Shell protocol."
ln crypto:ssh crypto.protocols sys:is_a
set.add name="ontology.cryptography" id="crypto:ssh"

def "crypto:tls" "Transport Layer Security protocol."
ln crypto:tls crypto.protocols sys:is_a
ln crypto:tls crypto:ca @requires
set.add name="ontology.cryptography" id="crypto:tls"

def "crypto:tokenization" "Replacing sensitive data with tokens."
ln crypto:tokenization crypto.data_encryption sys:is_a
set.add name="ontology.cryptography" id="crypto:tokenization"
