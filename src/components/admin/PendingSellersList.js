// src/components/admin/PendingSellersList.js
"use client";

import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchPendingSellers,
  approveSeller,
  rejectSeller,
  selectPendingSellers,
  selectSellersStatus,
  selectSellersError,
  selectSellerActionStatus,
} from "@/features/admin/sellersSlice";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

function SellerRow({ seller }) {
  const dispatch = useDispatch();
  const actionStatus = useSelector(selectSellerActionStatus(seller.id));
  const [rejectOpen, setRejectOpen] = useState(false);
  const [reason, setReason] = useState("");

  const isApproving = actionStatus === "approving";
  const isRejecting = actionStatus === "rejecting";
  const isBusy = isApproving || isRejecting;

  const handleApprove = () => {
    dispatch(approveSeller(seller.id));
  };

  const handleConfirmReject = () => {
    dispatch(rejectSeller({ seller_id: seller.id, reason }));
    setRejectOpen(false);
    setReason("");
  };

  return (
    <>
      <div className="flex items-center justify-between border rounded-lg px-4 py-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{seller.business_name}</span>
            <Badge variant="secondary">Pending</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {seller.full_name} · {seller.email}
          </p>
          <p className="text-xs text-muted-foreground">
            Applied {new Date(seller.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={isBusy}
            onClick={() => setRejectOpen(true)}
          >
            {isRejecting ? "Rejecting..." : "Reject"}
          </Button>
          <Button size="sm" disabled={isBusy} onClick={handleApprove}>
            {isApproving ? "Approving..." : "Approve"}
          </Button>
        </div>
      </div>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject {seller.business_name}?</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              This will delete the pending application. Optionally add a reason
              — it will be included in the notification email.
            </p>
            <Textarea
              placeholder="Reason (optional)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmReject}>
              Confirm reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default function PendingSellersList() {
  const dispatch = useDispatch();
  const sellers = useSelector(selectPendingSellers);
  const status = useSelector(selectSellersStatus);
  const error = useSelector(selectSellersError);

  useEffect(() => {
    dispatch(fetchPendingSellers());
  }, [dispatch]);

  if (status === "loading") {
    return <p className="text-sm text-muted-foreground">Loading pending sellers...</p>;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (sellers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No pending seller applications right now.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {sellers.map((seller) => (
        <SellerRow key={seller.id} seller={seller} />
      ))}
    </div>
  );
}