import React from "react";
import Button from "./Button";
import Modal from "./Modal";

interface ConfirmDialogProps {
    isVisible: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    title: string;
    message: React.ReactNode;
    confirmText?: string;
    cancelText?: string;
    confirmVariant?: "primary" | "secondary" | "danger";
    showCancelButton?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    isVisible,
    onConfirm,
    onCancel,
    title,
    message,
    confirmText = "Confirm",
    cancelText = "Cancel",
    confirmVariant = "danger",
    showCancelButton = true
}) => {
    return (
        <Modal isVisible={isVisible} onClose={onCancel} title={title}>
            <div className="mb-5">
                {typeof message === 'string' ? <p>{message}</p> : message}
                
                {confirmVariant === "danger" && typeof message === 'string' && (
                    <p className="mt-2 text-sm text-gray-600">This can not be undone.</p>
                )}
            </div>
            
            <div className="flex justify-between gap-3">
                {showCancelButton && (
                    <Button variant="secondary" onClick={onCancel}>{cancelText}</Button>
                )}
                    <Button variant={confirmVariant} onClick={onConfirm} className={showCancelButton ? "" : "w-full"}>{confirmText}</Button>
            </div>
        </Modal>
    );
};

export default ConfirmDialog;