<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use App\Models\User;
use App\Models\Department;

class StaffFactory extends Factory
{
    protected $model = \App\Models\Staff::class;

    public function definition(): array
    {
        return [
            'user_id' => User::factory(),
            'name' => $this->faker->name,
            'role' => $this->faker->randomElement(['Doctor','Nurse','Admin']),
            'specialization' => $this->faker->optional()->word,
            'phone' => $this->faker->phoneNumber,
            'department_id' => Department::factory(),
        ];
    }
}
