import React from "react";

import Calendar from "./Calendar";
import Nutrition from "./Nutrition";

const Account: React.FC = () => {
    return (
        <div className="flex flex-col">
            <div className="flex flex-col lg:flex-row lg:justify-center">
                <Calendar />
                <Nutrition />
            </div>
        </div>
    );
};

export default Account;