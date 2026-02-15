import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { PenTool, Check, Download, Shield, AlertCircle } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { showToast } from '../store/uiSlice';
import { signatureService } from '../services/signatureService';
import { generationService } from '../services/generationService';
import { contractService } from '../services/contractService';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';

function SignaturePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState([]);
  const [contract, setContract] = useState(null);
  const [signature, setSignature] = useState(null);
  const [verification, setVerification] = useState(null);
  const [signing, setSigning] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [signatureModal, setSignatureModal] = useState(false);
  const [signatureName, setSignatureName] = useState('');
  const [signatureError, setSignatureError] = useState('');

  const selectedContractId = id || null;

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const listRes = await contractService.getContracts(0, 20);
        if (!mounted) return;
        setContracts(listRes.contracts || []);

        if (!selectedContractId) {
          setLoading(false);
          return;
        }

        const [contractRes, signatureRes] = await Promise.all([
          contractService.getContract(selectedContractId),
          signatureService.getSignatureInfo(selectedContractId),
        ]);

        if (!mounted) return;
        setContract(contractRes);
        setSignature(signatureRes);
      } catch (err) {
        if (!mounted) return;
        const message = err.response?.data?.detail || err.message || 'Failed to load signature data';
        dispatch(showToast({ type: 'error', title: 'Load Failed', message }));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [dispatch, selectedContractId]);

  const refreshSignatureState = async (contractId) => {
    const res = await signatureService.getSignatureInfo(contractId);
    setSignature(res);
  };

  const handleSignDocument = async () => {
    if (!selectedContractId) return;
    if (!signatureName.trim() || signatureName.trim().length < 2) {
      setSignatureError('Please enter a valid full name');
      return;
    }

    setSigning(true);
    setSignatureModal(false);
    try {
      await signatureService.signContract(selectedContractId);
      dispatch(showToast({ type: 'success', title: 'Signed', message: 'Contract signed successfully.' }));
      await refreshSignatureState(selectedContractId);
      setVerification(null);
    } catch (err) {
      const detail = err.response?.data?.detail || '';
      if (typeof detail === 'string' && detail.includes('No generated contract version found')) {
        try {
          await generationService.generateFromContract(selectedContractId, 'pdf', true);
          await signatureService.signContract(selectedContractId);
          dispatch(showToast({ type: 'success', title: 'Generated + Signed', message: 'Generated latest version and signed it.' }));
          await refreshSignatureState(selectedContractId);
          setVerification(null);
        } catch (signErr) {
          const message = signErr.response?.data?.detail || signErr.message || 'Signing failed';
          dispatch(showToast({ type: 'error', title: 'Signing Failed', message }));
        }
      } else {
        const message = detail || err.message || 'Signing failed';
        dispatch(showToast({ type: 'error', title: 'Signing Failed', message }));
      }
    } finally {
      setSigning(false);
    }
  };

  const handleVerify = async () => {
    if (!selectedContractId) return;
    setVerifying(true);
    try {
      const res = await signatureService.verifySignature(selectedContractId);
      setVerification(res);
      dispatch(showToast({ type: res.is_valid ? 'success' : 'error', title: 'Verification Complete', message: res.verification_message }));
      await refreshSignatureState(selectedContractId);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Verification failed';
      dispatch(showToast({ type: 'error', title: 'Verification Failed', message }));
    } finally {
      setVerifying(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedContractId) return;
    try {
      const res = await contractService.downloadContract(selectedContractId);
      if (res?.download_url) {
        window.open(res.download_url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Download failed';
      dispatch(showToast({ type: 'error', title: 'Download Failed', message }));
    }
  };

  const signatureStatus = useMemo(() => {
    if (!signature?.has_signature) return 'pending';
    if (verification?.verification_outcome === 'revoked') return 'invalid';
    if (verification?.is_valid) return 'verified';
    if (signature?.status === 'signed') return 'signed';
    return signature?.status || 'pending';
  }, [signature, verification]);

  const getStatusBadge = (status) => {
    const map = {
      pending: { variant: 'warning', label: 'Pending' },
      signed: { variant: 'info', label: 'Signed' },
      verified: { variant: 'success', label: 'Verified' },
      invalid: { variant: 'error', label: 'Invalid' },
      revoked: { variant: 'error', label: 'Revoked' },
    };
    return map[status] || map.pending;
  };

  if (loading) {
    return <Card><p className="text-gray-600">Loading signature workspace...</p></Card>;
  }

  if (!selectedContractId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Digital Signature</h1>
          <p className="text-gray-600 mt-1">Choose a contract to sign or verify</p>
        </div>
        <Card>
          <div className="space-y-3">
            {contracts.length === 0 && <p className="text-gray-600">No contracts found. Upload a contract first.</p>}
            {contracts.map((c) => (
              <button
                key={c.id}
                onClick={() => navigate(`/signature/${c.id}`)}
                className="w-full text-left p-4 rounded-lg border hover:bg-gray-50"
              >
                <p className="font-semibold text-gray-900">{c.title || c.filename}</p>
                <p className="text-xs text-gray-600">{new Date(c.uploaded_at).toLocaleString()}</p>
              </button>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  const badge = getStatusBadge(signatureStatus);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Digital Signature</h1>
          <p className="text-gray-600 mt-1">{contract?.title || contract?.filename || 'Contract'}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2" onClick={handleDownload}>
            <Download className="w-4 h-4" style={{ color: '#4b5563' }} />
            Download
          </Button>
          <Link to="/signature">
            <Button variant="ghost">Switch Contract</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Signature Details</h2>
                <Badge variant={badge.variant}>{badge.label}</Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Signer</p>
                  <p className="font-medium text-gray-900">{signature?.signer?.name || '-'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Signed At</p>
                  <p className="font-medium text-gray-900">
                    {signature?.signed_at ? new Date(signature.signed_at).toLocaleString() : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Algorithm</p>
                  <p className="font-medium text-gray-900">{signature?.algorithm || '-'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Countersigners Pending</p>
                  <p className="font-medium text-gray-900">{signature?.pending_countersigners ?? 0}</p>
                </div>
              </div>

              {verification && (
                <div className="p-3 rounded-lg border bg-gray-50">
                  <p className="text-sm font-medium text-gray-900">Last Verification</p>
                  <p className="text-sm text-gray-700 mt-1">{verification.verification_message}</p>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              {!signature?.has_signature ? (
                <Button onClick={() => setSignatureModal(true)} className="w-full gap-2" loading={signing}>
                  <PenTool className="w-4 h-4" style={{ color: 'white' }} />
                  Sign Contract
                </Button>
              ) : (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-green-50 border border-green-200">
                  <Check className="w-5 h-5 text-green-600 mt-0.5" />
                  <p className="text-sm text-green-800">This contract already has a signature.</p>
                </div>
              )}

              <Button variant="outline" onClick={handleVerify} className="w-full gap-2" loading={verifying}>
                <Shield className="w-4 h-4" style={{ color: '#1f2937' }} />
                Verify Signature
              </Button>
            </div>
          </Card>

          <Card className="bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">About Digital Signatures</h3>
            <div className="space-y-2 text-xs text-gray-600">
              <p>• Uses RSA + SHA-256 verification flow in backend.</p>
              <p>• Signature metadata is audit-tracked.</p>
              <p>• If no generated version exists, app generates one before signing.</p>
            </div>
          </Card>
        </div>
      </div>

      <Modal
        isOpen={signatureModal}
        onClose={() => setSignatureModal(false)}
        title="Sign Document"
        size="md"
        footer={(
          <>
            <Button variant="outline" onClick={() => setSignatureModal(false)}>Cancel</Button>
            <Button onClick={handleSignDocument} className="gap-2" loading={signing}>
              <PenTool className="w-4 h-4" style={{ color: 'white' }} />
              Confirm Signature
            </Button>
          </>
        )}
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 shrink-0" />
              <p className="text-xs text-yellow-800">By signing, you accept this contract in the application workflow.</p>
            </div>
          </div>

          <Input
            label="Full Legal Name"
            placeholder="Enter your full name"
            value={signatureName}
            onChange={(e) => {
              setSignatureName(e.target.value);
              setSignatureError('');
            }}
            error={signatureError}
          />

          {signatureName.trim() && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-xs text-gray-600 mb-2">Signature Preview</p>
              <div className="border-b-2 border-blue-600 pb-2">
                <p className="text-3xl text-blue-600 font-signature">{signatureName}</p>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

export default SignaturePage;
